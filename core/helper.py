import os
import zipfile
from os.path import basename, join
from tempfile import TemporaryDirectory
from typing import Tuple

from django.core.files import File

from page.models import Page


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
	image_files = [i for i in all_files if os.path.splitext(i)[1] in ('.jpg', '.jpeg', '.png')]
	print(image_files)
	pages = []
	total = failed = 0
	for i in image_files:
		try:
			page = Page(
				language=language,
				category=category,
				parent=os.path.splitext(basename(i))[0].strip()
			)
			page.image.save(
				basename(i),
				File(open(i, 'rb')),
				save=False
			)
			pages.append(page)
		except:
			failed += 1
		finally:
			total += 1
	Page.objects.bulk_create(pages)
	return (total, failed)