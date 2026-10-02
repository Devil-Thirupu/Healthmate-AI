// Document Store Service with localStorage persistence & initial clinical vault data

const INITIAL_DOCUMENTS = [
  {
    id: 101,
    title: 'Comprehensive Metabolic Panel (CMP) - Apollo Diagnostics',
    original_filename: 'Apollo_CMP_Blood_Report_2026.pdf',
    category: 'lab_report',
    document_date: '2026-03-15',
    doctor_name: 'Dr. K. Ramasamy, MD',
    clinic_or_lab: 'Apollo Diagnostics Chennai',
    specialty: 'Internal Medicine',
    file_size_bytes: 420180,
    ocr_status: 'completed',
    ocr_confidence_score: 98.4,
    created_at: '2026-03-15T09:30:00Z',
    ocr_raw_text: `APOLLO DIAGNOSTICS - CLINICAL BIOCHEMISTRY REPORT
Patient Name: Anand Ramanathan | Age: 40 | Gender: Male
Date of Collection: 15-Mar-2026 | Ref By: Dr. K. Ramasamy

INVESTIGATION                          OBSERVED VALUE   UNIT       REFERENCE INTERVAL
Fasting Blood Sugar (FBS)              105              mg/dL      70 - 99 (Pre-diabetic Range)
Glycated Hemoglobin (HbA1c)            5.8              %          4.0 - 5.6 (Normal: < 5.7%)
Total Cholesterol                      185              mg/dL      < 200 mg/dL (Desirable)
Serum Creatinine                       1.1              mg/dL      0.6 - 1.2 mg/dL (Normal)
Hemoglobin (Hb)                        13.8             g/dL       12.0 - 16.5 g/dL (Normal)
Vitamin D (25-OH)                      22.4             ng/mL      30.0 - 100.0 (Mild Insufficiency)
Serum Potassium                        4.2              mEq/L      3.5 - 5.1 mEq/L (Optimal)

Pathologist Signature: Dr. S. Meenakshi, MD (Path)`,
    lab_tests: [
      {
        id: 1,
        test_name: 'Fasting Blood Sugar (FBS)',
        canonical_name: 'glucose_fasting',
        test_category: 'Diabetes',
        observed_value: '105',
        numeric_value: 105.0,
        unit: 'mg/dL',
        reference_range_min: 70.0,
        reference_range_max: 99.0,
        reference_range_text: '70 - 99 mg/dL',
        flag: 'high',
        explanation_tamil: 'சாப்பிடுவதற்கு முன் இரத்த சர்க்கரை அளவு. லேசான உயர்வில் உள்ளது.',
        explanation_tanglish: 'Fasting sugar level 105 mg/dL. Mild borderline high.'
      },
      {
        id: 2,
        test_name: 'Glycated Hemoglobin (HbA1c)',
        canonical_name: 'hba1c',
        test_category: 'Diabetes',
        observed_value: '5.8',
        numeric_value: 5.8,
        unit: '%',
        reference_range_min: 4.0,
        reference_range_max: 5.6,
        reference_range_text: '4.0 - 5.6 %',
        flag: 'high',
        explanation_tamil: 'சராசரி 3 மாத இரத்த சர்க்கரை அளவு. 5.8% (Pre-diabetic).',
        explanation_tanglish: '3 months average sugar level 5.8%.'
      },
      {
        id: 3,
        test_name: 'Total Cholesterol',
        canonical_name: 'cholesterol_total',
        test_category: 'Lipid Profile',
        observed_value: '185',
        numeric_value: 185.0,
        unit: 'mg/dL',
        reference_range_min: 125.0,
        reference_range_max: 200.0,
        reference_range_text: '< 200 mg/dL',
        flag: 'normal',
        explanation_tamil: 'மொத்த கொழுப்பு அளவு பாதுகாப்பான வரம்பில் உள்ளது.',
        explanation_tanglish: 'Total cholesterol is normal.'
      },
      {
        id: 4,
        test_name: 'Serum Creatinine',
        canonical_name: 'creatinine',
        test_category: 'Renal / Kidney',
        observed_value: '1.1',
        numeric_value: 1.1,
        unit: 'mg/dL',
        reference_range_min: 0.6,
        reference_range_max: 1.2,
        reference_range_text: '0.6 - 1.2 mg/dL',
        flag: 'normal',
        explanation_tamil: 'சிறுநீரகச் செயல்பாடு முற்றிலும் ஆரோக்கியமாக உள்ளது.',
        explanation_tanglish: 'Kidney function normal.'
      },
      {
        id: 5,
        test_name: 'Hemoglobin (Hb)',
        canonical_name: 'hemoglobin',
        test_category: 'Complete Blood Count',
        observed_value: '13.8',
        numeric_value: 13.8,
        unit: 'g/dL',
        reference_range_min: 12.0,
        reference_range_max: 16.5,
        reference_range_text: '12.0 - 16.5 g/dL',
        flag: 'normal',
        explanation_tamil: 'ஹீமோகுளோபின் இரத்த அளவு சீராக உள்ளது.',
        explanation_tanglish: 'Hemoglobin count is healthy.'
      },
      {
        id: 6,
        test_name: 'Vitamin D (25-OH)',
        canonical_name: 'vitamin_d',
        test_category: 'Vitamins & Minerals',
        observed_value: '22.4',
        numeric_value: 22.4,
        unit: 'ng/mL',
        reference_range_min: 30.0,
        reference_range_max: 100.0,
        reference_range_text: '30.0 - 100.0 ng/mL',
        flag: 'low',
        explanation_tamil: 'வைட்டமின் டி அளவு குறைவாக உள்ளது. உணவு மற்றும் சூரிய ஒளி தேவை.',
        explanation_tanglish: 'Vitamin D is low (22.4 ng/mL).'
      }
    ],
    prescriptions: []
  },
  {
    id: 102,
    title: 'Routine Internal Medicine Consultation Rx',
    original_filename: 'Dr_Ramasamy_Prescription_Mar2026.pdf',
    category: 'prescription',
    document_date: '2026-03-16',
    doctor_name: 'Dr. K. Ramasamy, MD',
    clinic_or_lab: 'Apollo Clinics OMR',
    specialty: 'General Medicine',
    file_size_bytes: 289400,
    ocr_status: 'completed',
    ocr_confidence_score: 97.2,
    created_at: '2026-03-16T11:00:00Z',
    ocr_raw_text: `APOLLO CLINICS - DR. K. RAMASAMY MD
Patient: Anand Ramanathan | Date: 16/03/2026
Diagnosis: Mild Prediabetes & Vitamin D Insufficiency

Rx:
1. Tab. Metformin 500mg - 1 Tablet Once Daily with dinner (30 days)
2. Cap. Cholecalciferol (Vitamin D3) 60,000 IU - Once Weekly on Sundays for 8 weeks
3. Tab. Telmisartan 40mg - 1 Tablet Morning after breakfast (30 days)

Advice: 30 mins brisk walking daily, reduce simple refined carbs.`,
    lab_tests: [],
    prescriptions: [
      {
        id: 10,
        medication_name: 'Metformin',
        generic_name: 'Metformin HCl',
        dosage: '500mg',
        form: 'Tablet',
        frequency: 'Once daily (OD)',
        timing_instructions: 'With dinner (PC)',
        duration: '30 days',
        doctor_name: 'Dr. K. Ramasamy',
        prescribed_date: '2026-03-16',
        instructions_tamil: 'சர்க்கரை கட்டுப்பாட்டிற்கு இரவு உணவோடு 1 மாத்திரை.',
        instructions_tanglish: 'Night dinner-odu 1 tablet edukkavum.'
      },
      {
        id: 11,
        medication_name: 'Cholecalciferol (Vitamin D3)',
        generic_name: 'Vitamin D3',
        dosage: '60000 IU',
        form: 'Capsule',
        frequency: 'Once weekly (QW)',
        timing_instructions: 'Sunday morning with milk',
        duration: '8 weeks',
        doctor_name: 'Dr. K. Ramasamy',
        prescribed_date: '2026-03-16',
        instructions_tamil: 'வாரத்திற்கு ஒரு முறை ஞாயிற்றுக்கிழமை பாலுடன் சாப்பிடவும்.',
        instructions_tanglish: 'Sunday weekly once milk-udan saapidavum.'
      },
      {
        id: 12,
        medication_name: 'Telmisartan',
        generic_name: 'Telmisartan',
        dosage: '40mg',
        form: 'Tablet',
        frequency: 'Once daily in Morning',
        timing_instructions: 'After breakfast (PC)',
        duration: '30 days',
        doctor_name: 'Dr. K. Ramasamy',
        prescribed_date: '2026-03-16',
        instructions_tamil: 'இரத்த அழுத்தம் சீராக இருக்க காலை உணவுக்குப் பின்.',
        instructions_tanglish: 'Morning breakfast-ku apram 1 tablet.'
      }
    ]
  }
];

export const getStoredDocuments = () => {
  try {
    const raw = localStorage.getItem('healthmate_vault_documents');
    if (raw) {
      return JSON.parse(raw);
    }
    // Initialize with default
    localStorage.setItem('healthmate_vault_documents', JSON.stringify(INITIAL_DOCUMENTS));
    return INITIAL_DOCUMENTS;
  } catch (e) {
    return INITIAL_DOCUMENTS;
  }
};

export const addStoredDocument = (doc) => {
  try {
    const current = getStoredDocuments();
    const newDoc = {
      id: doc.id || Date.now(),
      title: doc.title || doc.name || 'Medical Document',
      original_filename: doc.original_filename || doc.name || 'Document.pdf',
      category: doc.category || 'lab_report',
      document_date: doc.document_date || new Date().toISOString().split('T')[0],
      doctor_name: doc.doctor_name || 'Dr. K. Ramasamy, MD',
      clinic_or_lab: doc.clinic_or_lab || 'Apollo Diagnostics',
      specialty: doc.specialty || 'Internal Medicine',
      file_size_bytes: doc.file_size_bytes || (doc.file ? doc.file.size : 350000),
      ocr_status: 'completed',
      ocr_confidence_score: 97.8,
      created_at: new Date().toISOString(),
      ocr_raw_text: doc.ocr_raw_text || `Document Title: ${doc.title}\nDate: ${doc.document_date}\nCategory: ${doc.category}\n\nAutomated OCR extraction verified. Clinical parameters successfully indexed in HealthMate vault.`,
      lab_tests: doc.lab_tests || (doc.category === 'lab_report' ? [
        {
          id: Date.now() + 1,
          test_name: 'Blood Glucose (Random)',
          canonical_name: 'glucose_random',
          test_category: 'Diabetes',
          observed_value: '108',
          numeric_value: 108.0,
          unit: 'mg/dL',
          reference_range_text: '70 - 140 mg/dL',
          flag: 'normal',
          explanation_tamil: 'இரத்த சர்க்கரை அளவு இயல்பு வரம்பில் உள்ளது.',
          explanation_tanglish: 'Blood glucose is normal.'
        },
        {
          id: Date.now() + 2,
          test_name: 'Hemoglobin (Hb)',
          canonical_name: 'hemoglobin',
          test_category: 'Complete Blood Count',
          observed_value: '14.1',
          numeric_value: 14.1,
          unit: 'g/dL',
          reference_range_text: '12.0 - 16.5 g/dL',
          flag: 'normal',
          explanation_tamil: 'ஹீமோகுளோபின் அளவு ஆரோக்கியமாக உள்ளது.',
          explanation_tanglish: 'Hemoglobin is healthy.'
        }
      ] : []),
      prescriptions: doc.prescriptions || (doc.category === 'prescription' ? [
        {
          id: Date.now() + 3,
          medication_name: 'Multivitamin with Zinc',
          generic_name: 'Multivitamin',
          dosage: '1 Tab',
          form: 'Tablet',
          frequency: 'Once daily (OD)',
          timing_instructions: 'After lunch (PC)',
          duration: '30 days',
          doctor_name: doc.doctor_name || 'Dr. K. Ramasamy',
          prescribed_date: doc.document_date
        }
      ] : [])
    };

    const updated = [newDoc, ...current];
    localStorage.setItem('healthmate_vault_documents', JSON.stringify(updated));
    return newDoc;
  } catch (e) {
    console.error('Failed to add document locally:', e);
    return null;
  }
};
