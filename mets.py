#!/usr/bin/env python3

# Zeitungen und Zeitschriften, Zeitungen
# ubg-ihd-zuz, collection91307 (empty)
# mets.py oai @OAI-PMH/UB-Giessen ListIdentifiers --set ubg-ihd-zuz > ubg-ihd-zuz.list

import argparse

# import sickle
import os
import sys
from urllib.parse import parse_qs, urlparse

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import requests
from lxml import etree
from PIL import Image, ImageDraw, ImageFilter
from sickle import Sickle, oaiexceptions

NAMESPACES = {"mets": "http://www.loc.gov/METS/", "mods": "http://www.loc.gov/mods/v3"}
ALTO_NAMESPACES = {"alto": "http://www.loc.gov/standards/alto/ns-v2#"}
ALTO_NAMESPACES_V3 = {"alto": "http://www.loc.gov/standards/alto/ns-v3#"}
ALTO_NAMESPACES_V4 = {"alto": "http://www.loc.gov/standards/alto/ns-v4#"}


def parse_coords(element):
    return {
        "x": int(round(float(element.get("HPOS")))),
        "y": int(round(float(element.get("VPOS")))),
        "width": int(round(float(element.get("WIDTH")))),
        "height": int(round(float(element.get("HEIGHT")))),
    }


COLOR_MAP = {
    "TextBlock": "lightblue",
    "Illustration": "lightgreen",
    "GraphicalElement": "pink",
    "ComposedBlock": "lightyellow",
    "Table": "lavender",
    "default": "lightgray",  # for any undefined element types
}


def plot_layout(filename):
    tree = etree.parse(filename)

    # layout_elements = tree.xpath('//alto:Layout', namespaces={'alto': 'http://www.loc.gov/standards/alto/ns-v2#'})
    ns = ALTO_NAMESPACES
    layout_elements = tree.xpath("//alto:Layout", namespaces=ns)
    if not layout_elements:
        ns = ALTO_NAMESPACES_V3
        layout_elements = tree.xpath("//alto:Layout", namespaces=ns)
        if not layout_elements:
            ns = ALTO_NAMESPACES_V4
            layout_elements = tree.xpath("//alto:Layout", namespaces=ns)

    print(f"{layout_elements=}")
    for layout in layout_elements:
        # print(etree.tostring(layout, pretty_print=True).decode())
        for child in layout.xpath("./*", namespaces=ns):
            print(f"- Found child element: {etree.QName(child).localname}")
            for el in child.xpath("./*", namespaces=ns):
                print(f"  - Found child element: {etree.QName(el).localname}")

    # Create a new figure
    fig, ax = plt.subplots(figsize=(12, 8))
    min_x, min_y, max_x, max_y = float("inf"), float("inf"), 0, 0

    printspace_elements = tree.xpath("//alto:PrintSpace", namespaces=ns)
    for printspace in printspace_elements:
        ps_coords = parse_coords(printspace)
        ax.add_patch(
            patches.Rectangle(
                (ps_coords["x"], ps_coords["y"]),
                ps_coords["width"],
                ps_coords["height"],
                fill=False,
                edgecolor="black",
            )
        )

        # Update page boundaries
        min_x = min(min_x, ps_coords["x"])
        min_y = min(min_y, ps_coords["y"])
        max_x = max(max_x, ps_coords["x"] + ps_coords["width"])
        max_y = max(max_y, ps_coords["y"] + ps_coords["height"])

        for child in printspace.xpath("./*", namespaces=ns):
            print(f"- Found child element: {etree.QName(child).localname}")
            child_name = etree.QName(child).localname
            coords = parse_coords(child)

            # Get color for the element type
            color = COLOR_MAP.get(child_name, COLOR_MAP["default"])

            # Plot rectangle for the child element
            ax.add_patch(
                patches.Rectangle(
                    (coords["x"], coords["y"]),
                    coords["width"],
                    coords["height"],
                    fill=True,
                    facecolor=color,
                    alpha=0.5,
                )
            )

            # Add text label
            ax.text(
                coords["x"],
                coords["y"],
                child_name,
                fontsize=8,
                verticalalignment="bottom",
            )

    # Set the limits of the plot to match the page
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)

    # Invert y-axis because ALTO coordinates start from top-left
    ax.invert_yaxis()

    # Set aspect ratio to equal
    ax.set_aspect("equal", adjustable="box")

    # Add a legend
    legend_elements = [
        patches.Patch(facecolor=color, edgecolor="black", alpha=0.5, label=element)
        for element, color in COLOR_MAP.items()
    ]
    ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.1, 1))

    # Show the plot
    plt.title("ALTO XML Layout Visualization")
    plt.tight_layout()
    plt.show()

    # root = elementtree.getroot()
    # layout = root.find('Layout')
    # layout = root.find('/alto')
    # etree.indent(root)
    # print(etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=None).decode('UTF-8').strip())


def layout_command(args):
    print(f"{args=}")
    print("Verbose:", args.verbose)
    print("Dateien:", args.files)
    for filename in args.files:
        plot_layout(filename)


def blur_command(args):
    alto_file = args.alto
    image_file = args.image
    output_file = args.output
    blur_radius = 10

    # Parse the ALTO XML file
    tree = etree.parse(alto_file)

    # Open the image
    with Image.open(image_file) as img:
        # Create a drawing object
        draw = ImageDraw.Draw(img)

        # Find all Illustration elements
        illustration_elements = tree.xpath(
            "//alto:Illustration", namespaces=ALTO_NAMESPACES
        )

        # Process each Illustration element
        for illustration in illustration_elements:
            coords = parse_coords(illustration)

            # Bereich der Illustration ausschneiden
            region = img.crop(
                (
                    coords["x"],
                    coords["y"],
                    coords["x"] + coords["width"],
                    coords["y"] + coords["height"],
                )
            )

            # Ausgeschnittenen Bereich unscharf machen
            blurred_region = region.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            # Unscharfen Bereich wieder einfügen
            img.paste(blurred_region, (coords["x"], coords["y"]))

        # Modifiziertes Bild speichern
        img.save(output_file)


def makeblack_command(args):
    alto_file = args.alto
    image_file = args.image
    output_file = args.output

    # Parse the ALTO XML file
    tree = etree.parse(alto_file)

    # Open the image
    with Image.open(image_file) as img:
        # Create a drawing object
        draw = ImageDraw.Draw(img)

        # Find all Illustration elements
        illustration_elements = tree.xpath(
            "//alto:Illustration", namespaces=ALTO_NAMESPACES
        )

        # Process each Illustration element
        for illustration in illustration_elements:
            coords = parse_coords(illustration)

            # Draw a black rectangle over the illustration area
            draw.rectangle(
                [
                    (coords["x"], coords["y"]),
                    (coords["x"] + coords["width"], coords["y"] + coords["height"]),
                ],
                fill="black",
            )

        # Save the modified image
        img.save(output_file)

    print(f"Processed image saved as {output_file}")


def fix(filenames, inline):
    for filename in filenames:
        pass


def pretty(filenames):
    for filename in filenames:
        elementtree = etree.parse(filename)
        root = elementtree.getroot()
        mets = root.find(".//mets:mets", namespaces=NAMESPACES)
        # mets = root.find('.//mets:mets')
        if mets is not None:
            etree.indent(mets)
            with open(filename, "w") as fp:
                fp.write(
                    etree.tostring(
                        mets, encoding="UTF-8", pretty_print=True, xml_declaration=None
                    )
                    .decode("UTF-8")
                    .strip()
                )


def login(login_url, username, password):
    # Authenticate.
    r = requests.post(
        login_url, data={"loginUser": username, "loginPassword": password}
    )

    # Raise exception if r.status_code != requests.codes.ok.
    r.raise_for_status()

    # Session cookie is required for access to hidden OAI records and other data.
    print(f"{r.cookies=}")
    return r.cookies


def get_oai_api(args):
    if args.session_id is not None:
        cookies = dict(session_id=args.session_id)
        sickle = Sickle(args.oai_url, cookies=cookies)
    elif args.login_url is not None:
        # Use login authentication with session cookie for OAI-PMH.
        cookies = login(args.login_url, args.username, args.password)
        sickle = Sickle(args.oai_url, cookies=cookies)
    elif args.username is not None:
        # Use basic authentication for OAI-PMH.
        sickle = Sickle(args.oai_url, auth=(args.username, args.password))
    else:
        # Access OAI-PMH without any authentication.
        sickle = Sickle(args.oai_url)
    return sickle


def images_command(args):
    if args.session_id is not None:
        # Use an existing session cookie, skip login.
        cookies = dict(session_id=args.session_id)
    elif args.login_url is not None:
        # Use login authentication with session cookie.
        cookies = login(args.login_url, args.username, args.password)
    else:
        # No authentication (public images).
        cookies = None
    os.makedirs("max", exist_ok=True)
    for image in args.images:
        print(f"{image=}")
        filename = f"max/{image}.jpg"
        if os.path.exists(filename):
            continue
        r = requests.get(f"{args.image_url}/{image}", cookies=cookies)
        r.raise_for_status()
        with open(filename, "wb") as fp:
            for chunk in r.iter_content(chunk_size=4096):
                fp.write(chunk)


def format_command(args):
    print(f"{args=}")
    print("Verbose:", args.verbose)
    print("Pretty:", args.pretty)
    print("Dateien:", args.files)


def oai_get_record(args):
    print(f"{args=}")
    if not args.identifier and not args.identifiers:
        print("ERROR: kein Identifier angegeben (--identifier oder positionale Identifiers).")
        return
    sickle = get_oai_api(args)
    # print(f"{sickle=}")
    if args.metadataPrefix is None:
        args.metadataPrefix = "mets"
    if args.identifier:
        # Get a single METS record.
        record = sickle.GetRecord(
            identifier=args.identifier, metadataPrefix=args.metadataPrefix
        )
        if args.pretty:
            root = etree.fromstring(record.raw)
            if args.mets:
                root = root.find(".//mets:mets", namespaces=NAMESPACES)
            print(
                etree.tostring(
                    root, encoding="UTF-8", pretty_print=True, xml_declaration=None
                )
                .decode("UTF-8")
                .strip()
            )
        else:
            print(record.raw)

    # Iterate over all identifiers, get METS records and write them to files.
    for identifier in args.identifiers:
        filename = f"mets/{identifier}.xml"
        if os.path.exists(filename):
            continue
        try:
            record = sickle.GetRecord(
                identifier=identifier, metadataPrefix=args.metadataPrefix
            )
        except oaiexceptions.IdDoesNotExist:
            print(f"ERROR: id {identifier=} does not exist")
            continue
        dirname = os.path.dirname(filename)
        os.makedirs(dirname, exist_ok=True)
        """
  <mets:structMap TYPE="LOGICAL">
    <mets:div ID="log680731" DMDID="md680731" ADMID="amd680731" LABEL="Military government gazette Germany. 1945-1946" TYPE="newspaper" ORDER="1" CONTENTIDS="urn:nbn:de:bsz:mh40-994384">
      <mets:fptr FILEID="IMG_TEASER_681544"/>
      <mets:div ID="log680732" DMDID="md680732" ADMID="amd680732" LABEL="1 (1945)" TYPE="year" ORDER="1">
        <mets:mptr LOCTYPE="URL" xlink:href="https://druckschriften-digital.marchivum.de/oai/?verb=GetRecord&amp;metadataPrefix=mets&amp;identifier=680732"/>
        <mets:fptr FILEID="IMG_TEASER_681544"/>
      </mets:div>
      <mets:div ID="log680733" DMDID="md680733" ADMID="amd680733" LABEL="2 (1946)" TYPE="year" ORDER="2">
        <mets:mptr LOCTYPE="URL" xlink:href="https://druckschriften-digital.marchivum.de/oai/?verb=GetRecord&amp;metadataPrefix=mets&amp;identifier=680733"/>
        <mets:fptr FILEID="IMG_TEASER_681626"/>
      </mets:div>
    </mets:div>
  </mets:structMap>
        """
        root = etree.fromstring(record.raw)
        if args.recursive:
            struct_map = root.xpath(
                '//mets:structMap[@TYPE="LOGICAL"]', namespaces=NAMESPACES
            )
            if struct_map:
                struct_map = struct_map[0]
                mptrs = struct_map.xpath(".//mets:mptr", namespaces=NAMESPACES)
                pointers = [
                    mptr.get("{http://www.w3.org/1999/xlink}href")
                    for mptr in mptrs
                    if mptr.get("{http://www.w3.org/1999/xlink}href")
                ]
                for pointer in pointers:
                    parsed_url = urlparse(pointer)
                    query_params = parse_qs(parsed_url.query)
                    if "identifier" in query_params:
                        new_identifier = query_params["identifier"][0]
                        if not new_identifier in args.identifiers:
                            args.identifiers.append(new_identifier)

        with open(filename, "w") as fp:
            if args.pretty:
                if args.mets:
                    root = root.find(".//mets:mets", namespaces=NAMESPACES)
                fp.write(
                    etree.tostring(
                        root, encoding="UTF-8", pretty_print=True, xml_declaration=None
                    )
                    .decode("UTF-8")
                    .strip()
                )
            else:
                fp.write(record.raw)


def oai_identify(args):
    sickle = get_oai_api(args)
    identify = sickle.Identify()
    if args.pretty:
        root = etree.fromstring(identify.raw)
        print(
            etree.tostring(
                root, encoding="UTF-8", pretty_print=True, xml_declaration=None
            )
            .decode("UTF-8")
            .strip()
        )
    else:
        print(f"{identify}")


def oai_list_identifiers(args):
    if args.metadataPrefix is None:
        args.metadataPrefix = "mets"
    sickle = get_oai_api(args)
    try:
        items = sickle.ListIdentifiers(metadataPrefix=args.metadataPrefix, set=args.set)
    except oaiexceptions.NoRecordsMatch:
        print("No records match for request.")
        return
    for item in items:
        if args.pretty:
            root = etree.fromstring(item.raw)
            print(
                etree.tostring(
                    root, encoding="UTF-8", pretty_print=True, xml_declaration=None
                )
                .decode("UTF-8")
                .strip()
            )
        else:
            print(f"{item}")


def oai_list_metadata_formats(args):
    sickle = get_oai_api(args)
    for item in sickle.ListMetadataFormats():
        if args.pretty:
            root = etree.fromstring(item.raw)
            print(
                etree.tostring(
                    root, encoding="UTF-8", pretty_print=True, xml_declaration=None
                )
                .decode("UTF-8")
                .strip()
            )
        else:
            print(f"{item}")


def oai_list_records(args):
    sickle = get_oai_api(args)
    for item in sickle.ListRecords(metadataPrefix=args.metadataPrefix, set=args.set):
        if args.pretty:
            root = etree.fromstring(item.raw)
            print(
                etree.tostring(
                    root, encoding="UTF-8", pretty_print=True, xml_declaration=None
                )
                .decode("UTF-8")
                .strip()
            )
        else:
            print(f"{item}")


def oai_list_sets(args):
    sickle = get_oai_api(args)
    for set in sickle.ListSets():
        if args.pretty:
            root = etree.fromstring(set.raw)
            print(
                etree.tostring(
                    root, encoding="UTF-8", pretty_print=True, xml_declaration=None
                )
                .decode("UTF-8")
                .strip()
            )
        else:
            print(f"{set}")


def oai_command(args):
    if args.verbose:
        print(f"{args=}")
    if args.oai_command == "GetRecord":
        oai_get_record(args)
    elif args.oai_command == "Identify":
        oai_identify(args)
    elif args.oai_command == "ListIdentifiers":
        oai_list_identifiers(args)
    elif args.oai_command == "ListMetadataFormats":
        oai_list_metadata_formats(args)
    elif args.oai_command == "ListRecords":
        oai_list_records(args)
    elif args.oai_command == "ListSets":
        oai_list_sets(args)


def add_oai_arguments(parser):
    parser.add_argument(
        "--pretty", action="store_true", help="Formatiere für leichte Lesbarkeit."
    )


def add_oai_parser(subparsers, oai_command):
    oai_command_parser = subparsers.add_parser(oai_command, help=f"OAI {oai_command}.")
    add_oai_arguments(oai_command_parser)
    return oai_command_parser


def main():
    parser = argparse.ArgumentParser(
        description="Verarbeitung von METS-Dateien mit Nutzung von OAI-PMH.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Ausführliche Meldungen."
    )
    parser.add_argument("--version", action="version", version="%(prog)s 2.0")
    subparsers = parser.add_subparsers(
        title="Befehle", dest="command", help="Befehl.", required=True
    )

    layout_parser = subparsers.add_parser(
        "layout", help="Zeige Layout für METS-Dateien."
    )
    layout_parser.add_argument("files", nargs="+", help="Liste der METS-Dateien.")

    blur_parser = subparsers.add_parser("blur", help="Schwärze Abbildungen.")
    blur_parser.add_argument("alto", help="ALTO-Datei.")
    blur_parser.add_argument("image", help="Bilddatei.")
    blur_parser.add_argument("output", help="Ausgabedatei.")

    makeblack_parser = subparsers.add_parser("makeblack", help="Schwärze Abbildungen.")
    makeblack_parser.add_argument("alto", help="ALTO-Datei.")
    makeblack_parser.add_argument("image", help="Bilddatei.")
    makeblack_parser.add_argument("output", help="Ausgabedatei.")

    fix_parser = subparsers.add_parser("fix", help="Korrigiere METS-Dateien.")
    fix_parser.add_argument("files", nargs="+", help="Liste der METS-Dateien.")
    fix_parser.add_argument(
        "-i", action="store_true", help="Inline-Edit, schreibe Korrektur direkt zurück."
    )

    format_parser = subparsers.add_parser("format", help="Formatiere METS-Dateien.")
    format_parser.add_argument(
        "--pretty", action="store_true", help="Formatiere für leichte Lesbarkeit."
    )
    format_parser.add_argument("files", nargs="+", help="Liste der METS-Dateien.")

    images_parser = subparsers.add_parser("images", help="Hole Bilddateien.")
    # --oai-url ist nicht von `images` gebraucht; deklariert, damit die
    # gemeinsamen Quellen-Arg-Dateien (die auch für `oai` dienen)
    # unverändert übergeben werden können.
    images_parser.add_argument(
        "--oai-url", help="URL für OAI-PMH (hier nicht verwendet)."
    )
    images_parser.add_argument("--username", help="Benutzerkennung für OAI-PMH.")
    images_parser.add_argument("--password", help="Passwort für OAI-PMH.")
    images_parser.add_argument("--image-url", required=True, help="URL für Bilder.")
    images_auth = images_parser.add_mutually_exclusive_group()
    images_auth.add_argument("--login-url", help="URL für Authentisierung.")
    images_auth.add_argument("--session-id", help="session id für Authentisierung.")
    images_parser.add_argument(
        "images", nargs="+", help="Liste von Bild-Ids oder Bild-URLs."
    )

    oai_parser = subparsers.add_parser("oai", help="Führe OAI-Befehl aus.")
    oai_parser.add_argument("--oai-url", required=True, help="URL für OAI-PMH.")
    oai_parser.add_argument("--username", help="Benutzerkennung für OAI-PMH.")
    oai_parser.add_argument("--password", help="Passwort für OAI-PMH.")
    oai_parser.add_argument("--login-url", help="URL für Authentisierung.")
    oai_parser.add_argument("--session-id", help="session id für Authentisierung.")
    oai_subparsers = oai_parser.add_subparsers(
        title="OAI-Befehle",
        dest="oai_command",
        help="OAI-Befehl.",
        required=True,
    )

    oai_get_record_parser = add_oai_parser(oai_subparsers, "GetRecord")
    oai_get_record_parser.add_argument("--identifier")
    oai_get_record_parser.add_argument("--metadataPrefix")
    oai_get_record_parser.add_argument(
        "--mets", action="store_true", help="Extrahiere METS-Daten."
    )
    oai_get_record_parser.add_argument(
        "--recursive", action="store_true", help="Hole auch weitere Records (rekursiv)"
    )
    oai_get_record_parser.add_argument(
        "identifiers", nargs="*", help="Liste von Identifiern."
    )
    oai_identify_parser = add_oai_parser(oai_subparsers, "Identify")
    oai_list_identifiers_parser = add_oai_parser(oai_subparsers, "ListIdentifiers")
    oai_list_identifiers_parser.add_argument("--from")
    oai_list_identifiers_parser.add_argument("--until")
    oai_list_identifiers_parser.add_argument("--metadataPrefix")
    oai_list_identifiers_parser.add_argument("--set")
    oai_list_metadata_formats_parser = add_oai_parser(
        oai_subparsers, "ListMetadataFormats"
    )
    oai_list_records_parser = add_oai_parser(oai_subparsers, "ListRecords")
    oai_list_records_parser.add_argument("--from")
    oai_list_records_parser.add_argument("--until")
    oai_list_records_parser.add_argument("--metadataPrefix")
    oai_list_records_parser.add_argument("--set")
    oai_list_sets_parser = add_oai_parser(oai_subparsers, "ListSets")

    args = parser.parse_args()

    if args.command == "layout":
        layout_command(args)
    elif args.command == "blur":
        blur_command(args)
    elif args.command == "makeblack":
        makeblack_command(args)
    elif args.command == "format":
        format_command(args)
    elif args.command == "images":
        images_command(args)
    elif args.command == "oai":
        oai_command(args)
    else:
        print(f"Error: unknown command {args.command}")


if __name__ == "__main__":
    main()
