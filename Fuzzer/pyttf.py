#-------------------------------------------------------------------------------
# Name:        pyttf
# Purpose:
#
# Author:      Ng??i y?u d?u
#
# Created:     11/07/2015
# Copyright:   (c) Ng??i y?u d?u 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import struct
import mmap


class TTFFont ():

    REQUIRED_TABLES     = ['cmap', 'head', 'hhea', 'hmtx', 'maxp', 'name', 'post', 'OS/2']
    TTF_TABLES          = ['cvt', 'fpgm', 'glyf', 'loca', 'prep']
    POSTSCRIPT_TABLES   = ['CFF', 'VORG']
    BITMAP_TABLES       = ['EBDT', 'EBLC', 'EBSC']
    OPTIONAL_TABLES     = ['gasp', 'hdmx', 'kern' 'LTSH', 'PCLT', 'VDMX', 'vhea', 'vmtx']


    def __init__ (self, filename):
        self.map_file(filename)
        self.filename        = filename
        self.current_offset  = 0
        self.fontOffsetTable = FontOffsetTable(self.fontFileMap)
        self.current_offset  = self.current_offset + 0xC


        # Font table directories
        self.fontTableDirectories = {}

        # Read all tables
        for i in range(self.fontOffsetTable.numTables):
            table_entry = FontTableDirectory(self.fontFileMap, self.fontTableDirectories)
            self.fontTableDirectories[table_entry.tag] = table_entry
            self.current_offset = self.current_offset + 0x10


    def find_table(self, tableName):
        # Get table entry for this table
        tableTag = struct.unpack('>I', tableName)[0]
        table_entry =  self.fontTableDirectories[tableTag]
        return table_entry

    def map_file(self, filename):
        ''' Map font file for easy parser '''
        self.fontFile       = open(filename, 'rb')
        self.fontFileMap    = mmap.mmap(self.fontFile.fileno(), 0, access = mmap.ACCESS_READ + mmap.ACCESS_WRITE)

    def un_map_file(self):
        ''' Unmap mapped font file '''
        self.fontFileMap.close()
        self.fontFile.close()


'''
    Parse table directory
'''
class FontTableDirectory():

    def __init__(self, fontFileMap, fontTableDirectories):

        self.fontOffsetDirectoriesOffset = 0xC +  0x10 * len(fontTableDirectories)
        self.fontOffsetDirectories       = fontFileMap[self.fontOffsetDirectoriesOffset:]

        # Tag
        self.tag        = struct.unpack('>L', self.fontOffsetDirectories[0:4])[0]
        self.checksum   = struct.unpack('>L', self.fontOffsetDirectories[4:8])[0]
        self.offset     = struct.unpack('>L', self.fontOffsetDirectories[8:12])[0]
        self.length     = struct.unpack('>L', self.fontOffsetDirectories[12:16])[0]

        self.table      = None
        self.fontOffsetDirectories = fontTableDirectories


    def debug(self):
        print "Font table directory: %d" % len(self.fontOffsetDirectories)
        print "\tTag:\t\t\t0x%x"      % self.tag
        print "\tCheck sum:\t\t0x%x"  % self.checksum
        print "\tOffset:\t\t\t0x%x"   % self.offset
        print "\tLength:\t\t\t0x%x"   % self.length



'''
    The font header table
'''
class FontHeaderTable():

    def __init__(self, table_entry, fontFileMap):
        assert table_entry.tag == 0x68656164, "Invalid table tag"
        self.table_entry = table_entry

        self.fontHeaderTableMap = fontFileMap[self.table_entry.offset:]

        self.version            = struct.unpack('>I', self.fontHeaderTableMap[0:4])  [0]
        self.fontRevision       = struct.unpack('>I', self.fontHeaderTableMap[4:8])  [0]
        self.checkSumAdjustment = struct.unpack('>I', self.fontHeaderTableMap[8:12]) [0]
        self.magicNumber        = struct.unpack('>I', self.fontHeaderTableMap[12:16])[0]
        self.flags              = struct.unpack('>H', self.fontHeaderTableMap[16:18])[0]
        self.unitsPerEm         = struct.unpack('>H', self.fontHeaderTableMap[18:20])[0]
        self.created            = struct.unpack('>Q', self.fontHeaderTableMap[20:28])[0]
        self.modified           = struct.unpack('>Q', self.fontHeaderTableMap[28:36])[0]

        self.xMin               = struct.unpack('>H', self.fontHeaderTableMap[36:38])[0]
        self.yMin               = struct.unpack('>H', self.fontHeaderTableMap[38:40])[0]
        self.xMax               = struct.unpack('>H', self.fontHeaderTableMap[40:42])[0]
        self.yMax               = struct.unpack('>H', self.fontHeaderTableMap[42:44])[0]

        self.lowestRecPPEM      = struct.unpack('>H', self.fontHeaderTableMap[44:46])[0]
        self.fontDirectionHint  = struct.unpack('>H', self.fontHeaderTableMap[46:48])[0]
        self.indexToLocFormat   = struct.unpack('>H', self.fontHeaderTableMap[48:50])[0]
        self.glyphDataFormat    = struct.unpack('>H', self.fontHeaderTableMap[50:52])[0]

    def debug(self):
        print "Font Header table"
        print "\tVersion:\t\t\t0x%x"        % self.version
        print "\tFont revision:\t\t0x%x"    % self.fontRevision
        print "\tChecksum adjustment:0x%x"  % self.checkSumAdjustment
        print "\tMagic number:\t\t0x%x"     % self.magicNumber
        print "\tFlags\t\t\t\t0x%x"         % self.flags
        print "\tUnit per em:\t\t0x%x"      % self.unitsPerEm
        print "\tCreated time:\t\t0x%x"     % self.created
        print "\tModified time:\t\t0x%x"    % self.modified

        print "\txMin:\t\t\t\t0x%x"           % self.xMin
        print "\tyMin:\t\t\t\t0x%x"           % self.yMin
        print "\txMax:\t\t\t\t0x%x"           % self.xMax
        print "\tyMax:\t\t\t\t0x%x"           % self.yMax


        print "\tLowest Rec PPEM:\t0x%x"    % self.lowestRecPPEM
        print "\tFont Direction format:0x%x"% self.fontDirectionHint
        print "\tIndex to loc format:\t0x%x"  % self.indexToLocFormat
        print "\tGlyph data format:\t\t0x%x"  % self.glyphDataFormat










'''
    Parse font offset table
'''
class FontOffsetTable():

    def __init__(self, fontFileMap):

        self.fontOffsetTable = fontFileMap[:0xC]

        # sfnt
        self.SFNT_Ver       = struct.unpack('>I', self.fontOffsetTable[:4])[0]
        self.numTables      = struct.unpack('>H', self.fontOffsetTable[4:6])[0]
        self.searchRange    = struct.unpack('>H', self.fontOffsetTable[6:8])[0]
        self.entrySelector  = struct.unpack('>H', self.fontOffsetTable[8:10])[0]
        self.rangeShift     = struct.unpack('>H', self.fontOffsetTable[10:12])[0]


    def debug(self):
        print "Font Offset Table"
        print "\tsfnt version:\t\t 0x%x"     % self.SFNT_Ver
        print "\tNumber of tables:\t %d"     % self.numTables
        print "\tSearch range:\t\t%d"        % self.searchRange
        print "\tEntry selector:\t\t %d"     % self.entrySelector
        print "\tRange shift:\t\t%d"         % self.rangeShift





fontTTF = TTFFont('arial.ttf')
table_entry = fontTTF.find_table('head')
headTable   = FontHeaderTable(table_entry, fontTTF.fontFileMap)
headTable.debug()

fontTTF.un_map_file()




