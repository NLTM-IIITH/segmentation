from os.path import join

from django.contrib.auth import get_user_model
from django.db import models
from PIL import Image
from tqdm import tqdm

from core.models import BaseModel

from .managers import WordQuerySet

User = get_user_model()

class Point(BaseModel):
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)

    word = models.ForeignKey(
        'word.Word',
        on_delete=models.CASCADE,
    )

    class Meta:
        default_related_name = 'points'

    def __str__(self) -> str:
        return f'({self.x}, {self.y})'
    
    def __repr__(self) -> str:
        return f'<Point: {str(self)}>'



def get_image_path(instance, filename):
    return join(
        'Words',
        str(instance.page.category),
        str(instance.page.language),
        filename
    )


class Word(BaseModel):

    STATUS_CHOICES = (
        ('new', 'New'),
        ('cropped', 'Cropped'),
        ('sent_editing', 'Sent to Editing'),
        ('sent_verification', 'Sent to Verification'),
    )

    objects = WordQuerySet.as_manager()

    page = models.ForeignKey(
        'page.Page',
        on_delete=models.CASCADE,
    )

    image = models.ImageField(
        verbose_name='Word Image',
        help_text='original word level cropped image',
        null=True,
        blank=True,
        upload_to=get_image_path,
    )
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    w = models.IntegerField(default=0)
    h = models.IntegerField(default=0)
    line = models.IntegerField(default=0)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='new',
    )

    class Meta:
        default_related_name = 'words'

    def __repr__(self) -> str:
        return f'<Word: {self.status}>'

    def update_points(self, save: bool = True) -> list[Point]:
        ret = [
            Point(word=self, x=self.x, y=self.y),
            Point(word=self, x=self.x + self.w, y=self.y),
            Point(word=self, x=self.x + self.w, y=self.y + self.h),
            Point(word=self, x=self.x, y=self.y + self.h),
        ]
        if save:
            Point.objects.bulk_create(ret)
        return ret

    def convert_bbox_to_percentage(self):
        """
        Converts the absolute x,y,w,h pixelvalues to percent of total 
        width and height of the original image.
        """
        image = Image.open(self.page.image.path)
        width, height = image.width, image.height
        x = round(self.x / width * 100, 2)
        y = round(self.y / height * 100, 2)
        w = round(self.w / width * 100, 2)
        h = round(self.h / height * 100, 2)
        return (x,y,w,h)

    def convert_polygon_to_percentage(self):
        """
        Converts the points of the word to percent of total 
        width and height of the original image.

        Right now, owing to the fact of using TextPMs, we dont
        need to sort the points in a word in (counter)clockwise
        direction. But we may need to create a function to do that
        in the future.
        """
        image = Image.open(self.page.image.path)
        width, height = image.width, image.height
        ret = []
        for p in self.points.all(): # type: ignore
            ret.append([
                round(p.x / width * 100, 2),
                round(p.y / height * 100, 2)
            ])
        return ret


    def get_value(self):
        """
        function that is used by Page.get_annotations to get the proper
        value of each of the word.
        returns the json object as expected by the labelstudio frontend
        """
        value = {}
        if self.page.polygon:
            value = {
                'points': self.convert_polygon_to_percentage(),
                'polygonlabels': ['BBOX']
            }
        else:
            x,y,w,h = self.convert_bbox_to_percentage()
            value = {
                'x': x,
                'y': y,
                'width': w,
                'height': h,
                'rectanglelabels': ['BBOX'],
            }
        return {
            'id': str(self.id), # type: ignore
            'source': '$image',
            'from_name': 'tag',
            'to_name': 'img',
            'type': 'polygonlabels' if self.page.polygon else 'rectanglelabels',
            'value': value
        }

    def get_crop_coords(self) -> tuple[int, int, int, int]:
        x1 = self.x
        x2 = self.x + self.w
        y1 = self.y
        y2 = self.y + self.h
        return (x1, y1, x2, y2)

    def update_from_lsf(self, data, save=True) -> list[Point]:
        """
        this function takes as input the data object returned by the LSF
        for this particular word model instance.
        """
        width, height = data['original_width'], data['original_height']
        point_list = []
        if 'points' in data['value']:
            for point in data['value']['points']:
                point_list.append(
                    Point(
                        word=self,
                        x=(point[0] * width) // 100,
                        y=(point[1] * height) // 100
                    )
                )
            x = [i.x for i in point_list] # type: ignore
            y = [i.y for i in point_list] # type: ignore
            self.x = min(x)
            self.y = min(y)
            self.w = max(x) - min(x)
            self.h = max(y) - min(y)
        else:
            self.x = (data['value']['x'] * width) // 100
            self.y = (data['value']['y'] * height) // 100
            self.w = (data['value']['width'] * width) // 100
            self.h = (data['value']['height'] * height) // 100
            point_list = self.update_points(save=False)
        if save:
            Point.objects.bulk_create(point_list)
            self.save()
        return point_list

    @staticmethod
    def bulk_update_from_lsf(data, page) -> None:
        data_dict = {i['id']:i for i in data}
        ids = [i['id'] for i in data]
        words = []
        for i in range(len(ids)):
            words.append(
                Word(
                    page=page,
                )
            )
        Word.objects.bulk_create(words)
        print(f'Created {len(words)} word model placeholders')
        words = list(Word.objects.filter(page=page))
        points = []
        for i in tqdm(range(len(ids)), desc='Updating Words from LSF'):
            points += words[i].update_from_lsf(data_dict[ids[i]], save=False)
        Point.objects.bulk_create(points)
        Word.objects.bulk_update(words, ['x', 'y', 'w', 'h'])
        print('completed creating and updating new words')
