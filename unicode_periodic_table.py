from os import path, listdir, mkdir
from sys import stderr
from PIL import Image, ImageDraw, ImageFont
import unicodedataplus as unicodedata
from fontTools.ttLib import TTFont
import re
import argparse

HEIGHT=WIDTH=512
BORDER=10
MARGIN=10
INNER_MARGIN_HORIZONTAL = 20
INNER_MARGIN_BOTTOM = 80
INNER_MARGIN_TOP = 20
MAIN_FONT_SIZE=70

SCRIPT_FONT_SIZE=40
SMALL_SCRIPT_FONT_SIZE=30
CHARACTER_POSITION_TOP=80
CHARACTER_POSITION_BOTTOM=360
CODEPOINT_FONT_SIZES=[250,200,150,100,70,50,20]

logfile=open("logfile", "wt")

main_font = ImageFont.load_default(size=MAIN_FONT_SIZE)
script_font = ImageFont.load_default(size=SCRIPT_FONT_SIZE)
small_script_font  = ImageFont.load_default(size=SMALL_SCRIPT_FONT_SIZE)


def get_dims(font : ImageFont, s : str) -> (int, int):
	box=font.getbbox(s)
	return (box[2]-box[0],box[3]-box[1])

def log_and_print(msg : str) -> None:
	print (msg,file=stderr)
	logfile.write(msg+"\n")
	logfile.flush()

def has_glyph(font : TTFont, glyph : str) -> bool:
	for table in font['cmap'].tables:
		if glyph in table.cmap.keys():
			return True
	return False

def create_imagefont(codepoint : int, fontpath : str) -> ImageFont.FreeTypeFont:
	for size in CODEPOINT_FONT_SIZES:
		candidate_font_imagefont=ImageFont.truetype(
			fontpath,
			size=size
		)
		width,height=get_dims(candidate_font_imagefont,codepoint)
		if (
			width < WIDTH-2*(BORDER+MARGIN*2) and
			height < CHARACTER_POSITION_BOTTOM-CHARACTER_POSITION_TOP
		):
			return candidate_font_imagefont
	log_and_print("{} ({}) is too large for the smallest fontsize", 
		format_codepoint(ord(codepoint)),
		unicodedata.name(codepoint)
	)
	return candidate_font_imagefont
def format_codepoint(codepoint_num : int) -> str:
	fstring="U+{:04X}" if codepoint_num < 0x10000 else "U+{:06X}"
	return fstring.format(codepoint_num)
def has_font(codepoint_num : int) -> bool:
	# Fast Track for Ideographic Planes I am keeping disabled for now
	# if (codepoint_num >= 0x20000 and codepoint_num <= 0x3ffff):
	# 	candidate_font = TTFont(path.join('fonts',"NotoSansCJKsc-Medium.otf"))
	# 	if (has_glyph(candidate_font, codepoint_num)):
	# 		has_font.memoized_font_name="NotoSansCJKsc-Medium.otf"
	# 		has_font.memoized_font_ttf=candidate_font
	# 		return True
	# 	else: 
	# 		return False
	if (
		(has_font.memoized_font_ttf != None) and
		has_glyph(has_font.memoized_font_ttf, codepoint_num)
	):
		return create_imagefont(chr(codepoint_num),path.join('fonts',has_font.memoized_font_name))
	for fontfile in sorted(listdir("fonts")):	
		candidate_font = TTFont(path.join('fonts',fontfile))
		if (has_glyph(candidate_font, codepoint_num)):
			has_font.memoized_font_name=fontfile
			has_font.memoized_font_ttf=candidate_font
			return True
	return False

has_font.memoized_font_name=None
has_font.memoized_font_ttf=None

def find_font(codepoint_num : int) -> ImageFont.FreeTypeFont | None:
	#Fast Track for CJK Plane
	# if (codepoint_num >= 0x20000 and codepoint_num <= 0x3ffff):
	# 	candidate_font = TTFont(path.join('fonts',"NotoSansCJKsc-Medium.otf"))
	# 	if (has_glyph(candidate_font, codepoint_num)):
	# 		candidate_font_imagefont=create_imagefont(chr(codepoint_num),path.join('fonts',"NotoSansCJKsc-Medium.otf"))
	# 		find_font.memoized_font_name="NotoSansCJKsc-Medium.otf"
	# 		find_font.memoized_font_ttf=candidate_font
	# 		return candidate_font_imagefont
	# 	else: 
	# 		return None
	if (
		(find_font.memoized_font_ttf != None) and
		has_glyph(find_font.memoized_font_ttf, codepoint_num)
	):
		return create_imagefont(chr(codepoint_num),path.join('fonts',find_font.memoized_font_name))
	for fontfile in sorted(listdir("fonts")):	
		candidate_font = TTFont(path.join('fonts',fontfile))
		if (has_glyph(candidate_font, codepoint_num)):
			find_font.memoized_font_name=fontfile
			find_font.memoized_font_ttf=candidate_font
			return create_imagefont(chr(codepoint_num),path.join('fonts',fontfile))
	return None
find_font.memoized_font_name=None
find_font.memoized_font_ttf=None


def generate_image_for_codepoint(codepoint_num : int, puafont_name : str | None, generate_fontless : bool = True):
	codepoint = chr(codepoint_num)
	category = unicodedata.category(codepoint)
	image=Image.new("RGB", (WIDTH,HEIGHT), (255,255,255))
	ctx=ImageDraw.Draw(image)
	ctx.rectangle(
		[MARGIN, MARGIN, WIDTH-MARGIN, HEIGHT-MARGIN],
		outline=(0,0,0), width=BORDER
	)
	match category:
		case 'Cn' | 'Cs': 
			return None
		case 'Cc' | 'Cf':
			#Draw Light Blue Background
			ctx.rectangle(
				[MARGIN+BORDER, MARGIN+BORDER, WIDTH-(MARGIN+BORDER), HEIGHT-(MARGIN+BORDER)],
				fill=(216,255,255)
			)
			#Ascii Escape codes have their own symbol
			if (codepoint_num < 0x20):
				codepoint_font=ImageFont.truetype(
					path.join('fonts',"NotoSansSymbols2-Regular.ttf"),
					size=CODEPOINT_FONT_SIZES[0]
				)
				ctx.text(
					(WIDTH/2,CHARACTER_POSITION_BOTTOM),
					chr(codepoint_num+0x2400), fill=(0,0,0), font=codepoint_font, anchor="mb"
				)
			elif (codepoint_num == 0x7f):
				codepoint_font=ImageFont.truetype(
					path.join('fonts',"NotoSansSymbols2-Regular.ttf"),
					size=CODEPOINT_FONT_SIZES[0]
				)
				ctx.text(
					(WIDTH/2,CHARACTER_POSITION_BOTTOM),
					'\u2421', fill=(0,0,0), font=codepoint_font, anchor="mb"
				)
		case "Zs":
			#Spaces are drawn as blue rectangles to show their width.
			codepoint_font=ImageFont.truetype(
				path.join('fonts',"NotoSans-Regular.ttf"),
				size=CODEPOINT_FONT_SIZES[0]
			)
			space_width,space_height=get_dims(codepoint_font,codepoint)
			ctx.rectangle(
				[
					(WIDTH-space_width)/2,
					CHARACTER_POSITION_TOP+MARGIN+BORDER,
					(WIDTH+space_width)/2,
					CHARACTER_POSITION_BOTTOM
				],
				fill=(216,255,255)
			)

			#Ogham Space Special Case
			if (codepoint_num==0x1680): 
				codepoint_font=find_font(codepoint_num)
				ctx.text(
					(WIDTH/2,HEIGHT/2),
					"\u1680", fill=(50,50,50), font=codepoint_font, anchor="mb"
				)
		case _:
			
			if category == 'Co':
				fill=(100,50,127) 
				if (puafont_name != None):
					# Private Use Area Codepoints are drawn in Purple using The PUA font if specified
					codepoint_font=create_imagefont(codepoint,puafont_name)
				else:
					codepoint_font=find_font(codepoint_num)
			else:
				# Otherwise it's a dark gray
				fill=(50,50,50)
				codepoint_font=find_font(codepoint_num)

			#Draw Codepoint in the font found
			if (codepoint_font != None):
				ctx.text(
					(WIDTH/2,CHARACTER_POSITION_BOTTOM),
					codepoint, fill=fill, font=codepoint_font, anchor="mb"
				)
			else:
				#log_and_print(
				#	"{} ({}) is not supported by any font".format(format_codepoint(codepoint_num), unicodedata.name(codepoint))
				#)
				if not generate_fontless:
					return None

	#Draw Codepoint number at the bottom 
	ctx.text(
		(WIDTH/2, HEIGHT-(MARGIN+BORDER+INNER_MARGIN_BOTTOM)),
		format_codepoint(codepoint_num), fill=0, font=main_font, anchor="mt"
	)

	#Draw Category on top left
	ctx.text(
		(MARGIN+BORDER+INNER_MARGIN_HORIZONTAL, MARGIN+BORDER+INNER_MARGIN_TOP),
		category, fill=0, font=main_font, anchor="lt"
	)
	script=unicodedata.script(codepoint)
	
	#Usually it says "Unknown"
	if (category == "Co"):
		script="Private Use"
	#Get rid of underscores
	script=re.sub('_',' ', script)

	width,_ = get_dims(script_font, script)
	#Draw Script name on top Right
	if (width > 320):
		ctx.text(
			(WIDTH-(MARGIN+BORDER+INNER_MARGIN_HORIZONTAL), MARGIN+BORDER+INNER_MARGIN_TOP),
			script, fill=0, font=small_script_font, anchor="rt"
		)		
	else:
		ctx.text(
			(WIDTH-(MARGIN+BORDER+INNER_MARGIN_HORIZONTAL), MARGIN+BORDER+INNER_MARGIN_TOP),
			script, fill=0, font=script_font, anchor="rt"
		)
	return image


if __name__=="__main__":
	argparser = argparse.ArgumentParser(prog='unicode_periodic_table.py')
	argparser.add_argument("-r","--range",help="Enter Range as [hex]-[hex]")
	argparser.add_argument("--puafont", help="Font to use for private use area characters")
	argparser.add_argument("--generate_fontless", action=argparse.BooleanOptionalAction, help="Generate Images even if the font is missing characters")
	args = argparser.parse_args()
	range_match=None
	if (args.range != None):
		range_match=re.match(r"([0-9a-fA-F]+)-([0-9a-fA-F]+)",args.range)

	if (range_match):
		start=int(range_match[1],16)
		end=int(range_match[2],16)
	else:
		start=0
		end=0x110000
	if (args.puafont):
		puafont_name=args.puafont
	else:
		puafont_name=None
	if (not path.isdir("codepoint_images")):
		mkdir("codepoint_images")
	if (start < 0 or start > end or end > 0x110000 ):
		print("Range Error");
		exit(1)
	for codepoint_num in range(start,end):
		codepoint=chr(codepoint_num)
		category=unicodedata.category(codepoint)
		image=generate_image_for_codepoint(codepoint_num, puafont_name=puafont_name, generate_fontless=args.generate_fontless)
		if (image != None):
			print(f"codepoint_images/D+{codepoint_num:07}.png")
			image.save(f"codepoint_images/D+{codepoint_num:07}.png")
