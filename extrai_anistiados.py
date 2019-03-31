import csv
import re

import rows
from tqdm import tqdm


class BrazilianDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"


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
    for page in tqdm(pages, desc="2015"):
        table = rows.import_from_pdf(filename, page_numbers=(page,), starts_after=starts_after)
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
    for page in tqdm(pages, desc="2018"):
        page_data, merge = [], False
        for line in page.splitlines():
            lower = line.lower()
            if lower.startswith("n.ra") or lower.startswith("página") or lower.startswith("comissão"):
                continue
            if not merge:
                page_data.append(line)
            else:
                page_data[-1] = page_data[-1] + " " + line
            merge = len(line.split()) == 1

        for row in page_data:
            yield convert_row_2018(row)


if __name__ == "__main__":
    filename = "lista-anistiados-31-07-15.pdf"
    output_filename = "anistiados-2015.csv"
    with open(output_filename, mode="w") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=["requerimento", "data_publicacao", "numero_da_portaria", "cpf", "nome_do_anistiado"])
        writer.writeheader()
        for row in extract_2015(filename):
            writer.writerow(row)

    filename = "Pessoas anistiadas até outubro de 2018.pdf"
    output_filename = "anistiados-2018.csv"
    with open(output_filename, mode="w") as fobj:
        writer = csv.DictWriter(fobj, fieldnames="nra ano numero_sei nome_do_anistiado cpf data_publicacao_dou n_portaria".split())
        writer.writeheader()
        for row in extract_2018(filename):
            writer.writerow(row)
