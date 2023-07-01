from celery import shared_task

from page.models import Page


@shared_task
def send_to_verification(page_ids, version, modality):
	print('Got the send to verification request')
	Page.objects.filter(id__in=page_ids).send_to_verification(
		version,
		modality
	)