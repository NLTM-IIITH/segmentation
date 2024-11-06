import os
import zipfile
from os.path import basename, join, splitext
from tempfile import TemporaryDirectory
from typing import Tuple

from django.core.files import File
from django.http import FileResponse

from page.models import Page
from word.models import Point, Word


def handle_upload_zipfile(
	file,
	language: str,
	category: str,
) -> Tuple[int, int]:
	tmp = TemporaryDirectory()
	folder = tmp.name
	if type(file) == str:
		zip_path = file.strip()
	else:
		zip_path = join(folder, 'data.zip')
		print('Saving the ZIP')
		with open(zip_path, 'wb+') as f:
			for chunk in file.chunks():
				f.write(chunk)
	print('Extract the ZIP')
	with zipfile.ZipFile(zip_path, 'r') as f:
		f.extractall(folder)
	all_files = []
	for root, _, files in os.walk(folder):
		all_files += [join(root, i) for i in files]
	print(f'{len(all_files)} files present inside ZIP')
	all_files = [i for i in all_files if not i.endswith('zip')]
	image_files = [i for i in all_files if splitext(i)[1] in ('.jpg', '.jpeg', '.png')]
	txt_files = [i for i in all_files if splitext(i)[1] == '.txt']
	txt_files = {splitext(basename(i))[0]: i for i in txt_files}
	print(image_files)
	pages = []
	word_list = []
	point_list = []
	total = failed = 0
	for i in image_files:
		try:
			page = Page(
				language=language,
				category=category,
				parent=splitext(basename(i))[0].strip()
			)
			page.image.save(
				basename(i),
				File(open(i, 'rb')),
				save=False
			)
			try:
				if splitext(basename(i))[0] in txt_files:
					with open(txt_files[splitext(basename(i))[0]], 'r', encoding='utf-8') as f:
						a = f.read().strip().split('\n')
						a = [i.strip().split(',') for i in a]
						a = [list(map(int, i)) for i in a]
					for i in a:
						try:
							word = Word(
								page=page,
								x=i[0], y=i[1],
								w=i[2], h=i[3],
								line=i[4],
							)
							point_list += word.update_points(save=False)
							word_list.append(word)
						except Exception as e:
							print(i)
							raise e
							print(e)
					page.status = 'segmented'
			except Exception as e:
				raise e
				print(e)
			pages.append(page)
		except Exception as e:
			raise e
			failed += 1
		finally:
			total += 1
	Page.objects.bulk_create(pages)
	Word.objects.bulk_create(word_list)
	Point.objects.bulk_create(point_list)
	return (total, failed)


def download_pages(pages, folder_name, include_gt: bool = False, include_visual: bool = False):
	folder_name = folder_name.strip()
	while ' ' in folder_name:
		folder_name = folder_name.replace(' ', '_')
	while '.' in folder_name:
		folder_name = folder_name.replace('.', '')
	tmp = TemporaryDirectory(prefix='download')
	folder = join(tmp.name, folder_name)
	os.makedirs(folder)
	pages.export_all_language(folder, include_gt, include_visual)
	print('exporting the pages')
	os.system(f'cd {tmp.name} && zip -r {folder_name}.zip {folder_name} && cd -')
	return FileResponse(open(f'{folder}.zip', 'rb'))
