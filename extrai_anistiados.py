import csv
import re

import openpyxl
import rows
from rows.utils import slug
from tqdm import tqdm


class BrazilianDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"


class ISOOrBrazilianDecimalField(rows.fields.DecimalField):
    @classmethod
    def deserialize(cls, value):
        if "," in value:
            value = value.replace(".", "").replace(",", ".")
        return super().deserialize(value)


class ISOOrBrazilianDateField(rows.fields.DateField):
    @classmethod
    def deserialize(cls, value):
        if not (value or "").strip():
            return None
        elif " " in value:
            return value.split()[0]
        elif "/" in value:
            info = value.replace("/", "")
            return f"{info[4:]}-{info[2:4]}-{info[:2]}"
        else:
            raise RuntimeError(f"Invalid value: {repr(value)}")


class MonthDateField(rows.fields.DateField):
    @classmethod
    def deserialize(cls, value):
        if not (value or "").strip():
            return None
        elif " " in value:
            return value.split()[0]
        elif len(value) in (6, 7):
            value = value.replace("-", "").replace("/", "")
            return f"{value[-4:]}-{int(value[:-4]):02d}-01"
        else:
            raise RuntimeError(f"Invalid value: {repr(value)}")


def convert_row_2015(row):
    info = row.data_publicacao_dou_numero_da_portariacpfnome_do_anistiado.splitlines()
    info2 = info[1].split()
    cpf = info2[1]
    if set(cpf) == {"0"}:
        cpf = None
    return {
        "requerimento": row.requerimento,
        "data_publicacao": BrazilianDateField.deserialize(info[0]),
        "numero_da_portaria": info2[0],
        "cpf": cpf,
        "nome_do_anistiado": " ".join(info2[2:]),
    }


def extract_2015(filename):
    starts_after = re.compile(".*DE 13/11/2002")
    pages = range(1, rows.plugins.pdf.number_of_pages(filename) + 1)
    for page in tqdm(pages, desc=filename):
        table = rows.import_from_pdf(
            filename, page_numbers=(page,), starts_after=starts_after
        )
        for row in table:
            yield convert_row_2015(row)


def convert_row_2018(row):
    row = row.split()
    new = {}
    new["nra"] = row.pop(0)
    new["ano"] = row.pop(0)
    data = row.pop(0)
    if data.isdigit():
        new["numero_sei"] = data
    else:
        new["numero_sei"] = None
        row.insert(0, data)
    new["n_portaria"] = row.pop(-1)
    new["data_publicacao_dou"] = BrazilianDateField.deserialize(row.pop(-1))
    new["cpf"] = row.pop(-1)
    if not new["cpf"].isdigit():
        row.insert(0, new["cpf"])
        new["cpf"] = None
    new["nome_do_anistiado"] = " ".join(row)

    return new


def extract_2018(filename):
    pages = rows.plugins.pdf.pdf_to_text(filename)
    for page in tqdm(pages, desc=filename):
        page_data, merge = [], False
        for line in page.splitlines():
            lower = line.lower()
            if (
                lower.startswith("n.ra")
                or lower.startswith("página")
                or lower.startswith("comissão")
            ):
                continue
            if not merge:
                page_data.append(line)
            else:
                page_data[-1] = page_data[-1] + " " + line
            merge = len(line.split()) == 1

        for row in page_data:
            yield convert_row_2018(row)


def extract_servidor(filename):
    def load_data(filename):
        wb = openpyxl.load_workbook(filename, data_only=True, read_only=True)
        sheet = wb.active
        data, started = [], False
        for row in tqdm(sheet.rows, desc=filename):
            row = [str(cell.value or "") for cell in row[:8]]
            if row[0].lower().startswith("emitido"):
                continue
            if started or (not started and row[0] == "CPF do beneficiado"):
                started = True
                yield row

    data = load_data(filename)
    header = [slug(field_name) for field_name in next(data)]
    for row in data:
        row = dict(zip(header, row))
        row["valor"] = ISOOrBrazilianDecimalField.deserialize(row["valor"])
        row["data_inicio_da_percepcao"] = ISOOrBrazilianDateField.deserialize(
            row["data_inicio_da_percepcao"]
        )
        row["data_de_publicacao_da_portaria"] = ISOOrBrazilianDateField.deserialize(
            row["data_de_publicacao_da_portaria"]
        )
        row["mes_de_referencia"] = MonthDateField.deserialize(row["mes_de_referencia"])
        if set(row["cpf_do_beneficiado"]) == {"*"}:
            row["cpf_do_beneficiado"] = None
        yield row


def export_csv(input_filename, output_filename, field_names, function):
    with open(output_filename, mode="w") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=field_names)
        writer.writeheader()
        for row in function(input_filename):
            writer.writerow(row)


if __name__ == "__main__":
    export_csv(
        "lista-anistiados-31-07-15.pdf",
        "anistiados-2015.csv",
        "requerimento data_publicacao numero_da_portaria cpf nome_do_anistiado".split(),
        extract_2015,
    )

    export_csv(
        "Pessoas anistiadas até outubro de 2018.pdf",
        "anistiados-2018.csv",
        "nra ano numero_sei nome_do_anistiado cpf data_publicacao_dou n_portaria".split(),
        extract_2018,
    )

    export_csv(
        "beneficiados_lei10559.xlsx",
        "anistiados-servidor.csv",
        "cpf_do_beneficiado nome_do_beneficiado no_da_portaria data_de_publicacao_da_portaria data_inicio_da_percepcao valor mes_de_referencia tipo_de_prestacao".split(),
        extract_servidor,
    )
