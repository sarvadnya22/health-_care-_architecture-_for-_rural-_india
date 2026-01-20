<<<<<<< HEAD
SELECT chief_complaint, ai_prediction FROM triage_reports ORDER BY id DESC LIMIT 1;
=======
SELECT
    p.name AS PatientName,
    p.village,
    r.reading_type,
    r.value1,
    r.value2,
    tr.chief_complaint,
    tr.ai_prediction,
    pr.medication_name,
    ph.name AS PharmacyName
FROM
    patients p
LEFT JOIN
    readings r ON p.id = r.patient_id
LEFT JOIN
    triage_reports tr ON p.id = tr.patient_id
LEFT JOIN
    prescriptions pr ON p.id = pr.patient_id
LEFT JOIN
    pharmacies ph ON pr.dispensing_pharmacy_id = ph.id
WHERE
    p.name = 'Yogiraj Shinde';
>>>>>>> c3025e900aaa7513100e5c0ac0851b0b642f97bc
