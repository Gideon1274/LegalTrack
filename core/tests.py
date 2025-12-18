# pyright: reportAttributeAccessIssue=false, reportIndexIssue=false

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Case, CaseDocument, CustomUser


class Module2CaseWizardTests(TestCase):
    def setUp(self):
        self.lgu = CustomUser(
            email="lgu@example.com",
            role="lgu_admin",
            full_name="LGU Admin",
            lgu_municipality="Alcantara",
        )
        self.lgu.set_password("StrongPass123!")
        self.lgu.save()
        self.lgu.account_status = "active"
        self.lgu.save(update_fields=["account_status", "is_active"])

        self.client.login(username=self.lgu.username, password="StrongPass123!")  # noqa: S106

    def test_wizard_creates_case_and_allows_uploads(self):
        endorsement = SimpleUploadedFile("endorsement.txt", b"endorsement", content_type="text/plain")

        resp = self.client.post(
            reverse("submit_case"),
            {
                "client_name": "Juan Dela Cruz",
                "client_contact": "09123456789",
                "endorsement_letter": endorsement,
            },
        )
        self.assertEqual(resp.status_code, 302)

        case = Case.objects.get(client_name="Juan Dela Cruz")
        self.assertEqual(case.submitted_by_id, self.lgu.id)
        self.assertTrue(CaseDocument.objects.filter(case=case, doc_type="Endorsement Letter").exists())

        url_step2 = reverse("case_wizard", kwargs={"tracking_id": case.tracking_id, "step": 2})

        land_title = SimpleUploadedFile("land_title.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        tax_decl = SimpleUploadedFile("tax_declaration.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        resp2 = self.client.post(
            url_step2,
            {
                "form-TOTAL_FORMS": "5",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-doc_type": "Land Title",
                "form-0-required": "on",
                "form-0-file": land_title,
                "form-1-doc_type": "Tax Declaration",
                "form-1-required": "on",
                "form-1-file": tax_decl,
            },
        )
        self.assertEqual(resp2.status_code, 302)

        case.refresh_from_db()
        self.assertTrue(any(i.get("doc_type") == "Land Title" for i in case.checklist))
        self.assertTrue(CaseDocument.objects.filter(case=case, doc_type="Land Title").exists())

        url_step3 = reverse("case_wizard", kwargs={"tracking_id": case.tracking_id, "step": 3})
        resp3 = self.client.post(url_step3)
        self.assertEqual(resp3.status_code, 302)

    def test_edit_case_redirects_to_wizard_step1(self):
        case = Case.objects.create(client_name="A", client_contact="B", submitted_by=self.lgu)
        resp = self.client.get(reverse("edit_case", kwargs={"tracking_id": case.tracking_id}))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("case_wizard", kwargs={"tracking_id": case.tracking_id, "step": 1}), resp["Location"])


class Module2CapitolWorkflowTests(TestCase):
    def setUp(self):
        self.lgu = CustomUser(email="lgu2@example.com", role="lgu_admin", full_name="LGU Admin", lgu_municipality="Alcantara")
        self.lgu.set_password("StrongPass123!")
        self.lgu.save()
        self.lgu.account_status = "active"
        self.lgu.save(update_fields=["account_status", "is_active"])

        self.receiving = CustomUser(email="rec@example.com", role="capitol_receiving", full_name="Receiving")
        self.receiving.set_password("StrongPass123!")
        self.receiving.save()
        self.receiving.account_status = "active"
        self.receiving.save(update_fields=["account_status", "is_active"])

        self.examiner = CustomUser(email="exm@example.com", role="capitol_examiner", full_name="Examiner")
        self.examiner.set_password("StrongPass123!")
        self.examiner.save()
        self.examiner.account_status = "active"
        self.examiner.save(update_fields=["account_status", "is_active"])

        self.approver = CustomUser(email="apr@example.com", role="capitol_approver", full_name="Approver")
        self.approver.set_password("StrongPass123!")
        self.approver.save()
        self.approver.account_status = "active"
        self.approver.save(update_fields=["account_status", "is_active"])

        self.numberer = CustomUser(email="num@example.com", role="capitol_numberer", full_name="Numberer")
        self.numberer.set_password("StrongPass123!")
        self.numberer.save()
        self.numberer.account_status = "active"
        self.numberer.save(update_fields=["account_status", "is_active"])

        self.releaser = CustomUser(email="rel@example.com", role="capitol_releaser", full_name="Releaser")
        self.releaser.set_password("StrongPass123!")
        self.releaser.save()
        self.releaser.account_status = "active"
        self.releaser.save(update_fields=["account_status", "is_active"])

    def test_end_to_end_capitol_flow_to_release(self):
        case = Case.objects.create(client_name="Juan", client_contact="0912", submitted_by=self.lgu)

        self.client.login(username=self.receiving.username, password="StrongPass123!")  # noqa: S106
        resp = self.client.post(reverse("receive_case", kwargs={"tracking_id": case.tracking_id}))
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, "received")

        resp = self.client.post(
            reverse("assign_case", kwargs={"tracking_id": case.tracking_id}),
            {"examiner_id": str(self.examiner.id)},
        )
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, "in_review")
        self.assertEqual(case.assigned_to_id, self.examiner.id)

        self.client.logout()
        self.client.login(username=self.examiner.username, password="StrongPass123!")  # noqa: S106
        resp = self.client.post(reverse("submit_for_approval", kwargs={"tracking_id": case.tracking_id}))
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, "for_approval")

        self.client.logout()
        self.client.login(username=self.approver.username, password="StrongPass123!")  # noqa: S106
        resp = self.client.post(reverse("approve_case", kwargs={"tracking_id": case.tracking_id}))
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, "for_numbering")

        self.client.logout()
        self.client.login(username=self.numberer.username, password="StrongPass123!")  # noqa: S106
        resp = self.client.post(reverse("mark_numbered", kwargs={"tracking_id": case.tracking_id}))
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, "for_release")

        self.client.logout()
        self.client.login(username=self.releaser.username, password="StrongPass123!")  # noqa: S106
        resp = self.client.post(reverse("release_case", kwargs={"tracking_id": case.tracking_id}))
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, "released")
        self.assertIsNotNone(case.released_at)

    def test_approver_can_return_for_correction(self):
        case = Case.objects.create(client_name="Ana", client_contact="x", submitted_by=self.lgu, status="for_approval")

        self.client.login(username=self.approver.username, password="StrongPass123!")  # noqa: S106
        resp = self.client.post(
            reverse("return_for_correction", kwargs={"tracking_id": case.tracking_id}),
            {"reason": "Missing document"},
        )
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, "returned")
        self.assertEqual(case.return_reason, "Missing document")


class SuperuserCreationTests(TestCase):
    def test_create_superuser_does_not_require_username(self):
        su = CustomUser.objects.create_superuser(username="admin", email="admin@example.com", password="StrongPass123!Strong")
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_active)
        self.assertEqual(su.account_status, "active")
        self.assertEqual(su.role, "super_admin")
        self.assertTrue(bool(su.username))


class AuthenticationBackendsTests(TestCase):
    def test_staff_id_login_works(self):
        u = CustomUser(email="user1@example.com", role="lgu_admin", full_name="User One", lgu_municipality="Alcantara")
        u.set_password("StrongPass123!")
        u.save()
        u.account_status = "active"
        u.save(update_fields=["account_status", "is_active"])

        ok = self.client.login(username=u.username, password="StrongPass123!")  # noqa: S106
        self.assertTrue(ok)

    def test_email_login_is_rejected_except_admin_alias(self):
        u = CustomUser(email="user2@example.com", role="lgu_admin", full_name="User Two", lgu_municipality="Alcantara")
        u.set_password("StrongPass123!")
        u.save()
        u.account_status = "active"
        u.save(update_fields=["account_status", "is_active"])

        ok = self.client.login(username="user2@example.com", password="StrongPass123!")  # noqa: S106
        self.assertFalse(ok)

    def test_admin_email_alias_login_works_only_for_admin_gmail(self):
        admin = CustomUser(email="admin@gmail.com", role="super_admin", full_name="Admin")
        admin.set_password("StrongPass123!")
        admin.save()
        admin.account_status = "active"
        admin.is_staff = True
        admin.is_superuser = True
        admin.save(update_fields=["account_status", "is_active", "is_staff", "is_superuser"])

        ok = self.client.login(username="admin@gmail.com", password="StrongPass123!")  # noqa: S106
        self.assertTrue(ok)
