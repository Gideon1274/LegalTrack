from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Case, CaseDocument, CustomUser


class Module2CaseWizardTests(TestCase):
	def setUp(self):
		self.lgu = CustomUser(email='lgu@example.com', role='lgu_admin', full_name='LGU Admin')
		self.lgu.set_password('StrongPass123!')
		self.lgu.save()
		self.lgu.account_status = 'active'
		self.lgu.save(update_fields=['account_status', 'is_active'])

		self.client.login(username='lgu@example.com', password='StrongPass123!')

	def test_wizard_creates_case_and_allows_uploads(self):
		endorsement = SimpleUploadedFile('endorsement.txt', b'endorsement', content_type='text/plain')

		resp = self.client.post(reverse('submit_case'), {
			'client_name': 'Juan Dela Cruz',
			'client_contact': '09123456789',
			'endorsement_letter': endorsement,
		})
		self.assertEqual(resp.status_code, 302)

		case = Case.objects.get(client_name='Juan Dela Cruz')
		self.assertEqual(case.submitted_by_id, self.lgu.id)
		self.assertTrue(CaseDocument.objects.filter(case=case, doc_type='Endorsement Letter').exists())

		url_step2 = reverse('case_wizard', kwargs={'tracking_id': case.tracking_id, 'step': 2})

		land_title = SimpleUploadedFile('land_title.pdf', b'%PDF-1.4 test', content_type='application/pdf')
		resp2 = self.client.post(url_step2, {
			'form-TOTAL_FORMS': '5',
			'form-INITIAL_FORMS': '0',
			'form-MIN_NUM_FORMS': '0',
			'form-MAX_NUM_FORMS': '1000',
			'form-0-doc_type': 'Land Title',
			'form-0-required': 'on',
			'form-0-file': land_title,
			'form-1-doc_type': 'Tax Declaration',
			'form-1-required': 'on',
		})
		self.assertEqual(resp2.status_code, 302)

		case.refresh_from_db()
		self.assertTrue(any(i.get('doc_type') == 'Land Title' for i in case.checklist))
		self.assertTrue(CaseDocument.objects.filter(case=case, doc_type='Land Title').exists())

		url_step3 = reverse('case_wizard', kwargs={'tracking_id': case.tracking_id, 'step': 3})
		resp3 = self.client.post(url_step3)
		self.assertEqual(resp3.status_code, 302)

	def test_edit_case_redirects_to_wizard_step1(self):
		case = Case.objects.create(client_name='A', client_contact='B', submitted_by=self.lgu)
		resp = self.client.get(reverse('edit_case', kwargs={'tracking_id': case.tracking_id}))
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse('case_wizard', kwargs={'tracking_id': case.tracking_id, 'step': 1}), resp['Location'])
