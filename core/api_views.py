import base64
import json
from os.path import basename, join
from tempfile import TemporaryDirectory
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files import File
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from page.models import Page
from word.models import Word

User = get_user_model()


class BaseCoreView(LoginRequiredMixin):
    pass

@method_decorator(csrf_exempt, name='dispatch')
class FetchView(View):
    def get(self, *args, **kwargs):
        try:
            id = int(self.request.GET.get('id', 0))
            if not id:
                raise ValueError('PageID not valid')
            page = Page.objects.filter(parent=str(id))
            if not page.exists():
                raise ValueError('No page with this ID')
            if page.count() > 1:
                raise ValueError('Multiple pages found with this parent ID')
            page = page[0]
            if page.status not in ('corrected', 'skipped'):
                raise ValueError('Page not processed yet')
            return JsonResponse({
                'status': 'OK',
                'page': {
                    'status': page.status,
                    'words': page.words.all().to_dict()
                }
            })
        except ValueError as e:
            return JsonResponse({
                'status': 'ERR',
                'message': str(e),
            })
        except Exception as e:
            return JsonResponse({
                'status': 'ERR',
                'message': f'Unknown Exception: {str(e)}',
            })
        return JsonResponse({
            'status': 'OK',
            'message': f'PageID = {id}'
        })


@method_decorator(csrf_exempt, name='dispatch')
class UploadView(View):

    def post(self, *args, **kwargs):
        try:
            data = json.loads(self.request.body)
            if len(data) == 0:
                raise ValueError('No entries found')
            language = data['language']
            category = data['category']
            page_list = []
            word_list = []
            tmp = TemporaryDirectory()
            folder = tmp.name
            for i in data['images']:
                path = join(folder, str(uuid4()))
                page = Page(
                    language=language, category=category,
                    parent=str(i['parent']).strip(),
                )
                with open(path, 'wb') as f:
                    f.write(base64.b64decode(i['image']))
                page.image.save(
                    basename(path),
                    File(open(path, 'rb')),
                    save=False
                )
                page_list.append(page)
                if 'words' not in i:
                    continue
                for word in i['words']:
                    word_list.append(Word(
                        x=word['x'],
                        y=word['y'],
                        w=word['w'],
                        h=word['h'],
                        line=word['line'],
                        page=page
                    ))
                page.status = 'segmented'
            Page.objects.bulk_create(page_list)
            Word.objects.bulk_create(word_list)
            return JsonResponse({
                'status': 'OK',
                'message': f'Added {len(data["images"])} pages'
            })
        except ValueError as e:
            return JsonResponse({
                'status': 'ERR',
                'message': str(e),
            })
        except Exception as e:
            return JsonResponse({
                'status': 'ERR',
                'message': f'Unknown Exception: {str(e)}',
            })
