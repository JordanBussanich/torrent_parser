# Torrent Parser

This tool parses Torrent files and can search for keywords in them.

## What works?

This script will search for one or more strings or Regexes in one or more torrent files and produce a Tabulate table of the results. It can also just parse the torrent files and not search for keywords.

## What doesn't work?
- Outputting something that can be consumed by another program/script
- Outputting just the counts of each instance of a keyword

## Dependencies?

This script depends on 'tabulate' and 'fastbencode', pip install them as needed.
