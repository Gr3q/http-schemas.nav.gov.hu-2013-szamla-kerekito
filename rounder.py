#!/usr/bin/python

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Literal, Dict, Tuple, List

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


allowed_tags_to_edit = [
    "nettoar",
    "adoertek",
    "bruttoar",
    "nettoarossz",
    "afaertekossz",
    "bruttoarossz"
]

argparser = argparse.ArgumentParser(description='Kerekít minden számot (bruttó+nettó+áfa) az összesítés szekcióban (végösszeg+áfarovat) minden számlán egy "http://schemas.nav.gov.hu/2013/szamla" típusú xml fájlban.\
                                    A kerekítés szabványos módon megy végbe "*,50" alatt lefelé, "*,50" és afelett felfelé kerekítve.')
argparser.add_argument('input', type=Path, help='Az input xml fájl')
argparser.add_argument('--out_folder', type=Path, help='Az output xml mappa. Alapértermezett érték az input fájl mappája.', default=None)
argparser.add_argument('--force', type=bool, action=argparse.BooleanOptionalAction, default=False, help='Akkor is megpróbál kerekíteni ah ay inut fájl nem felel meg a várt formátumnak vagy hibás. Alapértelmezett érték: False.')
argparser.add_argument('--overwrite', type=bool, action=argparse.BooleanOptionalAction, default=False, help='Felülírja az output fájlt, ha már létezik. Alapértelmezett érték: False.',)
argparser.add_argument('--correct', type=str, choices=["netto", "afa"], default="netto", help='Kijavítja a az egyik részösszeget, ha nem egyezik a bruttó összegével. Alapértelmezett érték: netto.',)
args = argparser.parse_args()

input: Path = args.input
out_folder: Path | None = args.out_folder
overwrite: bool = args.overwrite
force: bool = args.force
correct: Literal["netto", "afa"]= args.correct

# Input file validation
if (not input.exists()):
    raise FileNotFoundError(f'Nem található a megadott input fájl: {input}')

if (not input.is_file()):
    raise FileNotFoundError(f'A megadott input nem fájl: {input}')

# Output folder validation
out_folder = out_folder if out_folder is not None else input.parent
if not out_folder.exists():
    out_folder.mkdir(parents=True)

out_path = out_folder.joinpath(f"{input.stem}-kerekitett{input.suffix}")

# XML validation
def get_xml_tree(input: Path) -> ET.ElementTree | None:
    try:
        tree = ET.parse(input)
        return tree
    except ET.ParseError:
        return None
    
def get_summary_part_values(element: ET.Element, variant: Literal["final_sum", "sum_part"]) -> Tuple[float | None, float | None, float | None]:
    before_tax_elem_name = "nettoar" if variant == "sum_part" else "nettoarossz"
    tax_elem_name = "adoertek" if variant == "sum_part" else "afaertekossz"
    after_tax_elem_name = "bruttoar" if variant == "sum_part" else "bruttoarossz"

    before_tax_elem = element.find(f'szamlak:{before_tax_elem_name}', namespaces)
    tax_elem = element.find(f'szamlak:{tax_elem_name}', namespaces)
    after_tax_elem = element.find(f'szamlak:{after_tax_elem_name}', namespaces)

    if (before_tax_elem is None or tax_elem is None or after_tax_elem is None):
        return (None, None, None)
    
    if (before_tax_elem.text is None or tax_elem.text is None or after_tax_elem.text is None):
        return (None, None, None)
    
    before_tax = float(before_tax_elem.text)
    tax = float(tax_elem.text)
    after_tax = float(after_tax_elem.text)

    return (before_tax, tax, after_tax)

def set_summary_part_value(element: ET.Element, variant: Literal["final_sum", "sum_part"], target: Literal["before_tax", "tax", "after_tax"], value: float) -> None:
    before_tax_elem_name = "nettoar" if variant == "sum_part" else "nettoarossz"
    tax_elem_name = "adoertek" if variant == "sum_part" else "afaertekossz"
    after_tax_elem_name = "bruttoar" if variant == "sum_part" else "bruttoarossz"

    elem_name = before_tax_elem_name if target == "before_tax" else tax_elem_name if target == "tax" else after_tax_elem_name

    elem = element.find(f'szamlak:{elem_name}', namespaces)
    if (elem is None):
        return
    
    elem.text = '{0:.2f}'.format(round(value))

tree = get_xml_tree(input)
if tree is None:
    print(f'A megadott input nem xml fájl: {input}')
    exit(1)

namespaces: Dict[str, str] = {
    'szamlak': 'http://schemas.nav.gov.hu/2013/szamla'
}

root = tree.getroot()
namespace = root.tag.split('}')[0][1:]
if (namespace != namespaces['szamlak']):
    print(f'A megadott input nem egy http://schemas.nav.gov.hu/2013/szamla xml fájl: {input}')
    if not force:
        exit(1)

    namespaces['szamlak'] = namespace
    print('Az input fájl nem felel meg a várt formátumnak, de a --force kapcsolóval megpróbálom kerekíteni.')

hadErrors = False
for invoice in root.findall('szamlak:szamla', namespaces):
    warnings: List[str] = []
    errors: List[str] = []
    invoice_id_elem = invoice.find('szamlak:fejlec/szamlak:szlasorszam', namespaces)
    paid_type_element = invoice.find('szamlak:nem_kotelezo/szamlak:fiz_mod', namespaces)
    paid_type = paid_type_element.text if paid_type_element is not None else None
    invoice_id = invoice_id_elem.text if invoice_id_elem is not None else None
    summary = invoice.find('szamlak:osszesites', namespaces)
    if summary is None:
        warnings.append(f'A számla nem tartalmaz összesítést')
        continue

    for summary_part in summary:
        final_sum = summary_part.tag.endswith('vegosszeg')
        for summary_item in summary_part:
            if summary_item.tag.split('}')[1] not in allowed_tags_to_edit:
                continue

            if summary_item.text is None:
                continue

            try:
                value = float(summary_item.text)
            except ValueError:
                print(f'A(z) {summary_item.tag} értéke nem szám: {summary_item.text}')
                if invoice_id is not None:
                    print(f'A számlaszám: {invoice_id}')
                exit(1)

            summary_item.text = '{0:.2f}'.format(round(value))

    try:
        # Parts validation
        tax_parts = summary.findall('szamlak:afarovat', namespaces)
        if (tax_parts is None):
            errors.append(f'A számla nem tartalmaz áfakulcsokat')
            continue

        tax_part_values: List[Tuple[float, float, float]] = []
        for [index, tax_part] in enumerate(tax_parts):
            before_tax, tax, after_tax = get_summary_part_values(tax_part, "sum_part")
            if (before_tax is None or tax is None or after_tax is None):
                errors.append(f'A számla nem tartalmaz nettó, áfa és bruttó összeget az áfakulcsoknál')
                continue

            if (before_tax + tax != after_tax):
                message = f'Áfakulcs#{index + 1} nem egyezik {after_tax} != {tax} + {before_tax}'

                if (correct == "netto"):
                    message += f', kijavítom a nettó összeget: {before_tax} -> {after_tax - tax}'
                    before_tax = after_tax - tax
                    set_summary_part_value(tax_part, "sum_part", "before_tax", value=after_tax - tax)

                elif (correct == "afa"):
                    message += f', kijavítom az áfa összeget: {tax} -> {after_tax - before_tax}'
                    tax = after_tax - before_tax
                    set_summary_part_value(tax_part, "sum_part", "tax", after_tax - before_tax)

                # If tax_parts has only 1 element, we will have a warning anyway with the final_sum because they are the same.
                # So we don't need to add the same warning twice. 
                if (len(tax_parts) > 1):
                    warnings.append(message)

            tax_part_values.append((before_tax, tax, after_tax))

        # Final sum validation
        final_sum = summary.find('szamlak:vegosszeg', namespaces)
        if (final_sum is None):
            errors.append(f'A számla nem tartalmaz végösszeget')
            continue

        before_tax, tax, after_tax = get_summary_part_values(final_sum, "final_sum")
        if (before_tax is None or tax is None or after_tax is None):
            errors.append(f'A számla nem tartalmaz nettó, áfa és bruttó végösszeget')
            continue

        if (before_tax + tax != after_tax):
            message = f'Végösszeg nem egyezik {after_tax} != {tax} + {before_tax}'
            if (correct == "netto"):
                message += f', kijavítom a nettó összeget: {before_tax} -> {after_tax - tax}'
                before_tax = after_tax - tax
                set_summary_part_value(final_sum, "final_sum", "before_tax", value=after_tax - tax)

            elif (correct == "afa"):
                message += f', kijavítom az áfa összeget: {tax} -> {after_tax - before_tax}'
                tax = after_tax - before_tax
                set_summary_part_value(final_sum, "final_sum", "tax", after_tax - before_tax)

            warnings.append(message)

        # Check if tax_parts and final_sum match
        tax_parts_after_tax_sum = sum(map(lambda x: x[2], tax_part_values))
        tax_parts_before_tax_sum = sum(map(lambda x: x[0], tax_part_values))
        tax_parts_tax_sum = sum(map(lambda x: x[1], tax_part_values))

        if (tax_parts_before_tax_sum != before_tax):
            message = f'Az áfakulcsok nettó összege nem egyezik a végösszeggel: {tax_parts_before_tax_sum} != {before_tax}'
            errors.append(message)

        if (tax_parts_tax_sum != tax):
            message = f'Az áfakulcsok áfa összege nem egyezik a végösszeggel: {tax_parts_tax_sum} != {tax}'
            errors.append(message)

        if (tax_parts_after_tax_sum != after_tax):
            message = f'Az áfakulcsok bruttó összege nem egyezik a végösszeggel: {tax_parts_after_tax_sum} != {after_tax}'
            errors.append(message)
    finally:
        if (len(errors) > 0 or len(warnings) > 0):
            print(f'\nSzámla problémák: {invoice_id} - {paid_type}')

            if (len(errors) > 0):
                hadErrors = True
                for error in errors:
                    print(f"{BColors.FAIL}{error}{BColors.ENDC}")

            elif (len(warnings) > 0):
                for warning in warnings:
                    print(f"{BColors.WARNING}{warning}{BColors.ENDC}")

if (not hadErrors):
    print(f'{BColors.OKGREEN}Nincs hiba a számlákban.{BColors.ENDC}')
else:
    print(f'{BColors.FAIL}Hibák a számlákban.{BColors.ENDC}')
    if not force:
        exit(1)

if (out_path.exists() and not overwrite):
    print(f'A megadott output fájl már létezik: {out_path}')
    exit(1)

# Output
tree.write(out_path, encoding='utf-8', xml_declaration=True, default_namespace=namespaces['szamlak'])
