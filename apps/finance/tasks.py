"""
Tâches Celery pour le module Finance.
Génération asynchrone des reçus PDF.
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, name="finance.generate_receipt_pdf", max_retries=3)
def generate_receipt_pdf(self, payment_id: int):
    """
    Génère le reçu PDF pour un paiement et l'enregistre.
    Appelée automatiquement après chaque enregistrement de paiement.
    Retries automatiques en cas d'échec (max 3 tentatives).
    """
    try:
        from .models import Payment, PaymentReceipt
        from apps.core.utils import generate_receipt_number

        payment = Payment.objects.select_related(
            "student", "school_year", "fee_config"
        ).get(id=payment_id)

        logger.info("Génération du reçu pour le paiement %s (%s)", payment_id, payment.reference)

        # Créer ou récupérer le reçu
        receipt, created = PaymentReceipt.objects.get_or_create(
            payment=payment,
            defaults={"receipt_number": generate_receipt_number("klass")}
        )

        # TODO Phase 5 : Génération PDF réelle avec ReportLab
        # from .pdf_generator import generate_payment_receipt_pdf
        # pdf_content = generate_payment_receipt_pdf(payment)
        # receipt.pdf_file.save(f"receipt_{receipt.receipt_number}.pdf", pdf_content)

        logger.info("Reçu %s créé avec succès (paiement %s)", receipt.receipt_number, payment_id)
        return {"receipt_number": receipt.receipt_number, "payment_id": payment_id}

    except Payment.DoesNotExist:
        logger.error("Paiement %s introuvable — reçu non généré", payment_id)
        raise

    except Exception as exc:
        logger.error("Erreur lors de la génération du reçu pour le paiement %s: %s", payment_id, exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="finance.send_payment_reminder")
def send_payment_reminder(student_id: int, fee_config_id: int):
    """
    Envoie un rappel de paiement à un élève/parent.
    Planifiée par Celery Beat.
    TODO Phase 5 : Implémentation SMS/WhatsApp via Africa's Talking.
    """
    logger.info(
        "Rappel de paiement — élève %s, frais %s",
        student_id,
        fee_config_id
    )
    # Placeholder — sera implémenté en Phase 5
    return {"status": "queued", "student_id": student_id}
