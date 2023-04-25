# Torrent Parser
# Hacked together by Jordan Bussanich

# Copyright (C) 2023  Jordan Bussanich

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import argparse
import sys
import re
import hashlib
import os

from abc import ABC, abstractmethod
from fastbencode import bencode, bdecode
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

class Searcher(ABC):
    @abstractmethod
    def search(self, content: str) -> bool:
        return
    
    def __init__(self, search_term: str, case_sensitive: bool) -> None:
        self.search_term = search_term
        self.case_sensitive = case_sensitive


class TextSearcher(Searcher):
    def search(self, content: str) -> bool:
        if self.case_sensitive:
            if self.search_term in content:
                return True
        else:
            if self.search_term.casefold() in str(content).casefold():
                return True
        
        return False

    def __init__(self, search_term: str, case_sensitive: bool) -> None:
        super().__init__(search_term, case_sensitive)


class RegexSearcher(Searcher):
    def search(self, content: str) -> bool:
        return bool(self.regex.match(content))

    def __init__(self, search_term: str, case_sensitive: bool) -> None:
        super().__init__(search_term, case_sensitive)

        if case_sensitive:
            self.regex = re.compile(search_term)
        else:
            self.regex = re.compile(search_term, re.IGNORECASE)       


class Torrent:
    def __init__(self) -> None:
        pass

    def __init__(self, announce: str,
                       announce_list: list[str],
                       comment: str,
                       created_by: str,
                       creation_date_unix: int,
                       length_bytes: int,
                       name: str,
                       piece_length_bytes: int,
                       pieces: str,
                       info_hash: str,
                       file_path: str):
        
        self.announce = announce
        self.announce_list = announce_list
        self.comment = comment
        self.created_by = created_by
        self.creation_date_utc = datetime.utcfromtimestamp(creation_date_unix)
        self.length_bytes = length_bytes
        self.name = name
        self.piece_length_bytes = piece_length_bytes
        self.pieces = pieces
        self.info_hash = info_hash
        self.file_path = file_path


    @classmethod
    def from_file(cls, torrent_path: str):
        with open(torrent_path, mode='rb') as f:
            torrent_file = f.read()

            decoded_torrent = bdecode(torrent_file)

            announce = decoded_torrent[b'announce'].decode('utf-8')
            announce_list = [a[0].decode('utf-8') for a in decoded_torrent[b'announce-list']]
            comment = decoded_torrent[b'comment'].decode('utf-8') if b'comment' in decoded_torrent else ''
            created_by = decoded_torrent[b'created by'].decode('utf-8')
            creation_date_unix = decoded_torrent[b'creation date']
            length_bytes = decoded_torrent[b'info'][b'length']
            name = decoded_torrent[b'info'][b'name'].decode('utf-8')
            piece_length_bytes = decoded_torrent[b'info'][b'piece length']
            pieces = decoded_torrent[b'info'][b'pieces']

            info_hash = hashlib.sha1(bencode(decoded_torrent[b'info'])).hexdigest()

            instance = cls(announce, announce_list, comment, created_by, creation_date_unix, length_bytes, name, piece_length_bytes, pieces, info_hash, torrent_path)

            return instance


class SearchResult:
    def __init__(self, search_term: str, result: str, field_name: str, torrent: Torrent) -> None:
        self.search_term = search_term
        self.result = result
        self.field_name = field_name
        self.torrent = torrent
    
    def __hash__(self) -> int:
        return hash((self.search_term, self.result, self.field_name, self.torrent))
    
    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, type(self)):
            return NotImplemented
        return self.search_term == __value.search_term and self.result == __value.result and self.field_name == __value.field_name and self.torrent == __value.torrent


parser = argparse.ArgumentParser(prog='torrent_parser',
                                 description='This program decodes torrent files and can perform keyword searches against them.')

parser.add_argument('-i', '--input',
                    help='The input Torrent file, or a directory containing Torrent files. If a directory is provided, it will be searched recursively.',
                    required=True,
                    dest='input_file')

parser.add_argument('-s', '--search-for',
                    help='The text you want to search for.',
                    dest='search_string')

parser.add_argument('-k', '--keyword-list',
                    help='A text file containing a single search term on each line. Do not use -s with -k.',
                    dest='keyword_list')

parser.add_argument( '--regex',
                    action='store_true',
                    help='Search using Regexs.')

parser.add_argument('--case-sensitive',
                    action='store_true',
                    help='Search for a case-sensitive string. Do not use this with --regex.')

parser.add_argument('--show-details',
                    action='store_true',
                    help='Show all of the decoded data, rather than just keyword matches.')

parser.add_argument('--search-pieces',
                    action='store_true',
                    help='Search the "pieces" field of the Torrent file(s)')

arguments = parser.parse_args()

keywords = list[str]()

if arguments.keyword_list:
    with open(arguments.keyword_list) as f:
        keywords.extend(f.read().splitlines())
else:
    if arguments.search_string:
        keywords.append(arguments.search_string)
    

if len(keywords) > 0:
    print('Searching for the following keywords:\n')
    print('\n'.join(keywords))
else:
    print('Not searching for keywords, just parsing the torrent file.')

print()

searchers = list[Searcher]()
for keyword in keywords:
    if arguments.regex:
        searchers.append(RegexSearcher(keyword, arguments.case_sensitive))
    else:
        searchers.append(TextSearcher(keyword, arguments.case_sensitive))

torrents = list[Torrent]()
if os.path.isdir(arguments.input_file):
    for torrent_file in Path(arguments.input_file).rglob('*.torrent'):
        torrents.append(Torrent.from_file(str(torrent_file)))
else:
    torrents.append(Torrent.from_file(arguments.input_file))

results = set[SearchResult]()
for torrent in torrents:
    for searcher in searchers:
        for attribute, value in torrent.__dict__.items():
            if not arguments.search_pieces and attribute == 'pieces':
                continue
            else:
                if type(value) is list:
                    for v in value:
                        if searcher.search(str(v)):
                            result = SearchResult(searcher.search_term, str(v), attribute, torrent)
                            results.add(result)
                else:
                    if searcher.search(str(value)):
                        result = SearchResult(searcher.search_term, str(value), attribute, torrent)
                        results.add(result)

rows = list()
headers = list()
if arguments.show_details:
    if arguments.search_pieces:
        rows = [[t.file_path, t.name, t.comment, t.info_hash, t.created_by, t.creation_date_utc, t.length_bytes, t.announce, t.announce_list, t.piece_length_bytes, t.pieces] for t in torrents]
        headers = ['Torrent Path', 'Name', 'Comment', 'Info Hash', 'Created By', 'Creation Date UTC', 'Length (bytes)', 'Announce', 'Announce List', 'Piece Length (bytes)', 'Pieces']
    else:
        rows = [[t.file_path, t.name, t.comment, t.info_hash, t.created_by, t.creation_date_utc, t.length_bytes, t.announce, t.announce_list, t.piece_length_bytes] for t in torrents]
        headers = ['Torrent Path', 'Name', 'Comment', 'Info Hash', 'Created By', 'Creation Date UTC', 'Length (bytes)', 'Announce', 'Announce List', 'Piece Length (bytes)']
else:
    rows = [[t.file_path, t.name, t.comment, t.info_hash] for t in torrents]
    headers = ['Torrent Path', 'Name', 'Comment', 'Info Hash']

print("Decoded the following torrents:")
print(tabulate(rows, headers=headers, tablefmt='mixed_outline'))
print()

if len(results) > 0:
    pass
    # if arguments.show_details:
    #     if arguments.search_pieces:
    #         rows = [[r.torrent.file_path] for r in results]]

    #         rows = [[t.file_path, t.name, t.comment, t.info_hash, t.created_by, t.creation_date_utc, t.length_bytes, t.announce, t.announce_list, t.piece_length_bytes, t.pieces] for t in torrents]
    #         headers = ['Torrent Path', 'Name', 'Comment', 'Info Hash', 'Created By', 'Creation Date UTC', 'Length (bytes)', 'Announce', 'Announce List', 'Piece Length (bytes)', 'Pieces']
    #     else:
    #         rows = [[t.file_path, t.name, t.comment, t.info_hash, t.created_by, t.creation_date_utc, t.length_bytes, t.announce, t.announce_list, t.piece_length_bytes] for t in torrents]
    #         headers = ['Torrent Path', 'Name', 'Comment', 'Info Hash', 'Created By', 'Creation Date UTC', 'Length (bytes)', 'Announce', 'Announce List', 'Piece Length (bytes)']
else:
    print("Did not find any search terms in any torrents.")