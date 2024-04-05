import os
import zipfile
from os.path import basename, join
from tempfile import TemporaryDirectory
from typing import Tuple

from django.core.files import File
from django.http import FileResponse

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


def download_pages(pages, folder_name, include_gt: bool = False, include_visual: bool = False):
	tmp = TemporaryDirectory(prefix='download')
	folder = join(tmp.name, folder_name)
	os.makedirs(folder)
	pages.export_all_language(folder, include_gt, include_visual)
	os.system(f'cd {tmp.name} && zip -r {folder_name}.zip {folder_name} && cd -')
	return FileResponse(open(f'{folder}.zip', 'rb'))


# def process_ver_edit(word, id, ocr):
# 	ret = [word.x, word.y, word.w, word.h]
# 	a = list(filter(lambda x:x['parent_id']==str(id), edit))
# 	if len(a) != 1:
# 		ret += [ocr, 0]
# 		return ','.join(list(map(str, ret)))
# 	a = a[0]
# 	if a['status'] == 'edited':
# 		ret += [a['ocr'], 1]
# 		return ','.join(list(map(str, ret)))
# 	else:
# 		ret += [a['ocr'], 0]
# 		return ','.join(list(map(str, ret)))

# def process_ver(word):
# 	ret = [word.x, word.y, word.w, word.h]
# 	a = list(filter(lambda x:x['parent_id']==str(word.id), ver))
# 	if len(a) != 1:
# 		return ''
# 	a = a[0]
# 	if a['status'] == 'correct':
# 		ret += [a['ocr'], 1]
# 		return ','.join(list(map(str, ret)))
# 	elif a['status'] in ('wrong', 'skip') and a['sent_to_editing']:
# 		return process_ver_edit(word, a['id'], a['ocr'])
# 	else:
# 		return ''

# def process_edit(word):
# 	ret = [word.x, word.y, word.w, word.h]
# 	a = list(filter(lambda x:x['parent_id']==str(word.id), edit))
# 	if len(a) != 1:
# 		return ''
# 	a = a[0]
# 	if a['status'] == 'edited':
# 		ret += [a['ocr'], 1]
# 		return ','.join(list(map(str, ret)))
# 	else:
# 		ret += [a['ocr'], 0]
# 		return ','.join(list(map(str, ret)))

# # def process_word(word):
# # 	ret = [word.x, word.y, word.w, word.h]
# # 	x = str(word.id)
# # 	if x in final:
# # 		ret += [final[x]['ocr'], '1' if final[x]['status'] in ('correct', 'edited') else '0']
# # 		return ','.join(list(map(str, ret)))
# # 	else:
# # 		return ''

# # def process_word(word):
# # 	if word.status == 'sent_verification':
# # 		return process_ver(word)
# # 	elif word.status == 'sent_editing':
# # 		return process_edit(word)
# # 	else:
# # 		return ''


# words = Word.objects.filter(page__category='ilocr_crowd_hw', page__status='sent')
# words = list(words)
# wordss = []
# for i in tqdm(wordss):
# 	wordss.append({
# 		'x': i.x, 'y': i.y, 'w': i.w, 'h': i.h,
# 		'id': i.id, 'pid': i.page.id
# 	})

# # =============START HERE===========================

# with open('../ocr.json', 'r', encoding='utf-8') as f:
# 	final = json.loads(f.read())

# def process_word(word):
# 	ret = [word['x'], word['y'], word['w'], word['h']]
# 	x = str(word['id'])
# 	if x in final:
# 		ret += [final[x]['ocr'], '1' if final[x]['status'] in ('correct', 'edited') else '0']
# 		return ','.join(list(map(str, ret)))
# 	else:
# 		return ''

# pw = {}
# for i in tqdm(wordss, desc='formulating pw'):
# 	if i['pid'] in pw:
# 		pw[i['pid']].append(i)
# 	else:
# 		pw[i['pid']] = [i]

# for i in tqdm(pw, desc='completing pw'):
# 	pw[i] = '\n'.join(list(map(process_word, pw[i])))

# pages = Page.objects.filter(category='ilocr_crowd_hw', status='sent')
# pages = list(pages)
# pages = [{'id': i.id, 'path': i.image.path.strip(), 'parent': i.parent.strip(), 'language': i.language.strip()} for i in pages]

# with open('../user.json', 'r') as f:
# 	user = json.loads(f.read())

# from PIL import Image


# def process_page(page):
# 	id = page['id']
# 	try:
# 		ret = pw[id]
# 		job_id = str(page['parent'])
# 		userid = str(user[job_id])
# 		lang = page['language']
# 		user_folder = join('/home/annotation/dataset/ilocr_crowd_hw', lang, userid)
# 		if not os.path.exists(user_folder):
# 			os.makedirs(user_folder)
# 		Image.open(page['path']).convert('RGB').save(
# 			join(user_folder, f'{job_id}.jpg')
# 		)
# 		with open(join(user_folder, f'{job_id}.txt'), 'w', encoding='utf-8') as f:
# 			f.write(ret)
# 	except Exception as e:
# 		print(f'Error while processing: {id}')

# test = pages[:20]
# for i in tqdm(test, desc='Processing pages'):
# 	process_page(i)