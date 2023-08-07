import logging

from celery import shared_task

from page.models import Page

logger = logging.getLogger(__name__)


@shared_task
def send_to_verification(page_ids, version, modality):
	logger.debug('Got the send to verification request')
	Page.objects.filter(id__in=page_ids).send_to_verification( # type: ignore
		version,
		modality
	)

@shared_task
def perform_segment_bulk(page_ids):
	logger.debug(f'Performing segment for {len(page_ids)} pages')
	Page.objects.filter(id__in=page_ids).segment_bulk() # type: ignore

@shared_task
def crowd_send(count: int = 1_000):
	logger.debug('Tranfering the crowd_hw pages to verification/editing')
	pages = Page.objects.filter(
		category='crowd_hw',
		status='corrected'
	).order_by('?')[:count]
	completed = 1
	errors = []
	for page in pages:
		logger.warn(f'[{completed}/{count}] Processing {page.language.title()} page')
		try:
			page.send_to_editing_verification()
		except:
			logger.error('Some error occured while sending.')
			errors.append(page.id)
		completed += 1
	logger.warn(errors)
	logger.warn(f'Sent the {count} pages to editing/verification')
	logger.warn(f'Encounter {len(errors)} while sending. find the list of error ids previously')

@shared_task
def ilocr_crowd_send(count: int = 1_000):
	logger.debug('Tranfering the ilocr_crowd_hw pages to verification/editing')
	pages = Page.objects.filter(
		category='ilocr_crowd_hw',
		status='corrected',
		qc_status='approved',
	).order_by('language')[:count]
	completed = 1
	errors = []
	for page in pages:
		logger.warn(f'[{completed}/{count}] Processing {page.language.title()} page')
		try:
			page.send_to_editing_verification()
		except Exception:
			logger.error('Some error occured while sending.')
			errors.append(page.id)
		completed += 1
	logger.warn(errors)
	logger.warn(f'Sent the {count} pages to editing/verification')
	logger.warn(f'Encounter {len(errors)} while sending. find the list of error ids previously')