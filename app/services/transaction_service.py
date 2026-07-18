from sqlalchemy import text
from sqlalchemy.orm import Session


def get_sample_transactions(
    db: Session,
    bank_id: int,
    response_code: str | None,
):
    query = text("""
        SELECT
            tr.masked_pan,
            tr.request_time,
            TIMESTAMPDIFF(SECOND, tr.request_time, tr.response_time) AS time_taken,
            tr.request_amount / 100 AS amount,
            tr.response_code,
            tr.retrieval_reference_number,
            adtr.rrn,
            tr.terminal_id,
            tr.sink_card_acceptor_id AS card_acceptor_id

        FROM transaction_record tr

        LEFT JOIN aptpay_dcir_transaction_record adtr
            ON tr.id = adtr.transaction_record_id

        LEFT JOIN card_bin cb
            ON LEFT(tr.masked_pan, 6) = cb.bin

        WHERE tr.mti = '0200'
        AND cb.bank_id = :bank_id
        AND (:response_code IS NULL OR tr.response_code = :response_code)
        AND tr.request_time >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
        ORDER BY tr.id DESC
        LIMIT 10
    """)

    result = db.execute(
        query,
        {
            "bank_id": bank_id,
            "response_code": response_code,
        },
    )

    return result.mappings().all()