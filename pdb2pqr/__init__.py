"""PDB2PQR

This package takes a PDB file as input and performs optimizations before
yielding a new PDB-style file as output.

For more information, see http://www.poissonboltzmann.org/
"""
from sys import version_info
assert version_info >= (3, 5)
import logging
from pathlib import Path
CONFIG_PATH = Path("config.json")
with open(CONFIG_PATH, "rt") as config_file:
    CONFIG = json.load(config_file)
from . import config
from . import run
from . import utilities




_LOGGER = logging.getLogger("PDB2PQR"+CONFIG["version"])
logging.captureWarnings(True)


def print_splash_screen(args):
    """Print argument overview and citation information.

    Args:
        args:  argparse namespace
    """
    _LOGGER.debug("Args:  %s", args)
    _LOGGER.info(CONFIG["title_format_string"].format(version=CONFIG["version"]))
    for citation in CONFIG["citations"]:
        _LOGGER.info(citation)


def check_files(args):
    """Check for other necessary files.

    Args:
        args:  argparse namespace
    Raises:
        FileNotFoundError:  necessary files not found
        RuntimeError:  input argument or file parsing problems
    """
    if args.usernames is not None:
        usernames = Path(args.usernames)
        if not usernames.is_file():
            error = "User-provided names file does not exist: %s" % usernames
            raise FileNotFoundError(error)

    if args.userff is not None:
        userff = Path(args.userff)
        if not userff.is_file():
            error = "User-provided forcefield file does not exist: %s" % userff
            raise FileNotFoundError(error)
        if args.usernames is None:
            raise RuntimeError('--usernames must be specified if using --userff')
    elif args.ff is not None:
        if utilities.test_dat_file(args.ff) == "":
            raise RuntimeError("Unable to load parameter file for forcefield %s" % args.ff)

    if args.ligand is not None:
        ligand = Path(args.ligand)
        if not ligand.is_file():
            error = "Unable to find ligand file: %s" % ligand
            raise FileNotFoundError(error)


def check_options(args):
    """Sanity check options.

    Args:
        args:  argparse namespace
    Raises:
        RuntimeError:  silly option combinations were encountered.
    """
    if (args.ph < 0) or (args.ph > 14):
        raise RuntimeError(("Specified pH (%s) is outside the range [1, 14] "
                            "of this program") % args.ph)

    if args.neutraln and (args.ff is None or args.ff.lower() != 'parse'):
        raise RuntimeError('--neutraln option only works with PARSE forcefield!')

    if args.neutralc and (args.ff is None or args.ff.lower() != 'parse'):
        raise RuntimeError('--neutralc option only works with PARSE forcefield!')


def print_pqr(args, pqr_lines, header_lines, missing_lines, is_cif):
    """Print output to specified file

    TODO - move this to another module (utilities)

    Args:
        args:  argparse namespace
        pqr_lines:  output lines (records)
        header_lines:  header lines
        missing_lines:  lines describing missing atoms (should go in header)
        is_cif:  flag indicating CIF-format
    """
    with open(args.output_pqr, "wt") as outfile:
        # Adding whitespaces if --whitespace is in the options
        if header_lines:
            _LOGGER.warning("Ignoring %d header lines in output.", len(header_lines))
        if missing_lines:
            _LOGGER.warning("Ignoring %d missing lines in output.", len(missing_lines))
        for line in pqr_lines:
            if args.whitespace:
                if line[0:4] == 'ATOM':
                    newline = line[0:6] + ' ' + line[6:16] + ' ' + \
                        line[16:38] + ' ' + line[38:46] + ' ' + line[46:]
                    outfile.write(newline)
                elif line[0:6] == 'HETATM':
                    newline = line[0:6] + ' ' + line[6:16] + ' ' + \
                        line[16:38] + ' ' + line[38:46] + ' ' + line[46:]
                    outfile.write(newline)
                elif line[0:3] == "TER" and is_cif:
                    pass
            else:
                if line[0:3] == "TER" and is_cif:
                    pass
                else:
                    outfile.write(line)
        if is_cif:
            outfile.write("#\n")


def main(args):
    """Main driver for running program from the command line.

    Validate inputs, launch PDB2PQR, handle output.

    Args:
        args:  argument namespace object (e.g., as returned by argparse).
    """
    logging.basicConfig(level=getattr(logging, args.log_level))
    print_splash_screen(args)
    check_files(args)
    pdblist, is_cif = utilities.get_molecule(args.input_path)

    # TODO - I wish this could be handled by argparse logic
    if args.assign_only or args.clean:
        args.debump = False
        args.opt = False
    check_options(args)

    results = run.run_pdb2pqr(pdblist, args, is_cif)

    print_pqr(args=args, pqr_lines=results["lines"], header_lines=results["header"],
              missing_lines=results["missed_ligands"], is_cif=is_cif)

    if args.apbs_input:
        utilities.dump_apbs(args.output_pqr)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.captureWarnings(True)
