% ESTE ARCHIVO ES GENERADO. Edite data/knowledge_base.json desde la aplicación.
% MediLogic - base de hechos y reglas de inferencia.
:- module(medilogic, [symptom/4, disease/6, medication/3, disease_symptom/2,
           disease_medication/2, contraindication/4, severity_weight/2,
           diagnosis_metrics/6, matched_symptom/5, urgency/4,
           medication_evaluation/8, activated_rule/4]).
:- use_module(library(lists)).
:- dynamic symptom/4, disease/6, medication/3, disease_symptom/2,
           disease_medication/2, contraindication/4.

% Hechos del catálogo
symptom('tos', "Tos", "Irritación o expulsión de aire de las vías respiratorias.", false).
symptom('congestion_nasal', "Congestión nasal", "Obstrucción o sensación de nariz tapada.", false).
symptom('dolor_garganta', "Dolor de garganta", "Molestia o dolor al tragar.", false).
symptom('fiebre', "Fiebre", "Elevación de la temperatura corporal.", true).
symptom('dificultad_respirar', "Dificultad para respirar", "Sensación de falta de aire o respiración trabajosa.", true).
symptom('estornudos', "Estornudos", "Expulsión brusca de aire por nariz y boca.", false).
symptom('dolor_cabeza', "Dolor de cabeza", "Dolor o presión en la cabeza.", false).
symptom('presion_alta', "Presión arterial elevada", "Lectura elevada de presión arterial registrada previamente.", true).
symptom('mareo', "Mareo", "Sensación de inestabilidad o aturdimiento.", false).
symptom('dolor_muscular', "Dolor muscular", "Dolor generalizado en músculos.", false).

disease('resfriado_comun', "Resfriado común", "Infección respiratoria viral frecuente de evolución generalmente leve.", 'respiratorio', 'viral', false).
disease('influenza', "Influenza", "Infección respiratoria viral que puede presentar fiebre y dolor muscular.", 'respiratorio', 'viral', false).
disease('rinitis_alergica', "Rinitis alérgica", "Respuesta alérgica que afecta principalmente las vías respiratorias superiores.", 'respiratorio', 'inmunologico', false).
disease('hipertension', "Hipertensión arterial", "Antecedente de presión arterial elevada que requiere seguimiento profesional.", 'cardiovascular', 'cronico', true).
disease_symptom('resfriado_comun', 'tos').
disease_symptom('resfriado_comun', 'congestion_nasal').
disease_symptom('resfriado_comun', 'dolor_garganta').
disease_symptom('resfriado_comun', 'estornudos').
disease_symptom('influenza', 'fiebre').
disease_symptom('influenza', 'tos').
disease_symptom('influenza', 'dolor_muscular').
disease_symptom('influenza', 'dolor_garganta').
disease_symptom('rinitis_alergica', 'estornudos').
disease_symptom('rinitis_alergica', 'congestion_nasal').
disease_symptom('rinitis_alergica', 'tos').
disease_symptom('hipertension', 'presion_alta').
disease_symptom('hipertension', 'dolor_cabeza').
disease_symptom('hipertension', 'mareo').
disease_medication('resfriado_comun', 'paracetamol').
disease_medication('resfriado_comun', 'loratadina').
disease_medication('resfriado_comun', 'ibuprofeno').
disease_medication('influenza', 'paracetamol').
disease_medication('influenza', 'ibuprofeno').
disease_medication('rinitis_alergica', 'loratadina').
disease_medication('hipertension', 'losartan').

medication('paracetamol', "Paracetamol", "Candidato sintético para aliviar fiebre y dolor; no es una prescripción médica.").
medication('ibuprofeno', "Ibuprofeno", "Candidato sintético antiinflamatorio; requiere revisión profesional de contraindicaciones.").
medication('loratadina', "Loratadina", "Candidato sintético antihistamínico para síntomas alérgicos.").
medication('losartan', "Losartán", "Candidato sintético asociado al antecedente de hipertensión en este prototipo.").
medication('warfarina', "Warfarina", "Tratamiento actual de ejemplo para probar incompatibilidades.").
contraindication('ibuprofeno', 'chronic_condition', 'hipertension', "Se excluye en este prototipo cuando existe hipertensión como antecedente.").
contraindication('ibuprofeno', 'treatment', 'warfarina', "Se excluye en este prototipo por incompatibilidad con warfarina.").

% Reglas de ponderación y diagnóstico
severity_weight(leve, 1).
severity_weight(moderado, 2).
severity_weight(severo, 3).

patient_symptom(PatientSymptoms, Symptom, Severity) :-
    member(sintoma(Symptom, Severity), PatientSymptoms).

matched_symptom(Disease, PatientSymptoms, Symptom, Severity, Weight) :-
    disease_symptom(Disease, Symptom),
    patient_symptom(PatientSymptoms, Symptom, Severity),
    severity_weight(Severity, Weight).

diagnosis_metrics(Disease, PatientSymptoms, Points, MaxPoints, Affinity, MatchCount) :-
    findall(Weight, matched_symptom(Disease, PatientSymptoms, _, _, Weight), Weights),
    sum_list(Weights, Points),
    findall(Symptom, disease_symptom(Disease, Symptom), Symptoms),
    length(Symptoms, SymptomCount),
    length(Weights, MatchCount),
    MaxPoints is SymptomCount * 3,
    ( MaxPoints > 0 ->
        RawAffinity is (Points / MaxPoints) * 100,
        Rounded is round(RawAffinity * 100) / 100,
        Affinity is min(100, Rounded)
    ; Affinity is 0 ).

% Reglas de urgencia. La bandera de alarma tiene prioridad sobre la severidad.
urgency(PatientSymptoms, inmediata, consulta_inmediata, sintoma_severo_o_alarma) :-
    ( member(sintoma(_, severo), PatientSymptoms) ;
      ( member(sintoma(AlarmSymptom, _), PatientSymptoms),
        symptom(AlarmSymptom, _, _, true) ) ), !.
urgency(PatientSymptoms, observacion, observacion_recomendada, sintomas_moderados) :-
    member(sintoma(_, moderado), PatientSymptoms), !.
urgency(PatientSymptoms, automanejo, posible_automanejo_orientativo, solo_sintomas_leves) :-
    PatientSymptoms \= [],
    forall(member(sintoma(_, Severity), PatientSymptoms), Severity = leve), !.
urgency(_, sin_datos, solicitar_datos, datos_insuficientes).

% Reglas de seguridad de medicamentos. El orden expresa la primera causa de descarte.
medication_evaluation(Medication, _, Allergies, _, _, descartado, alergia, Medication) :-
    member(Medication, Allergies), !.
medication_evaluation(Medication, _, _, ChronicConditions, _, descartado, chronic_condition, Condition) :-
    contraindication(Medication, chronic_condition, Condition, _),
    member(Condition, ChronicConditions), !.
medication_evaluation(Medication, Disease, _, _, _, descartado, disease, Disease) :-
    contraindication(Medication, disease, Disease, _), !.
medication_evaluation(Medication, _, _, _, Treatments, descartado, treatment, Treatment) :-
    contraindication(Medication, treatment, Treatment, _),
    member(Treatment, Treatments), !.
medication_evaluation(_, _, _, _, _, seguro, seguro, ninguno).

% Trazabilidad: cada solución se asocia a reglas legibles por la aplicación.
activated_rule(Disease, PatientSymptoms, coincidencia_de_sintomas, puntos_ponderados) :-
    diagnosis_metrics(Disease, PatientSymptoms, Points, _, _, _), Points > 0.
activated_rule(Disease, PatientSymptoms, severidad_ponderada, severidad_aplicada) :-
    matched_symptom(Disease, PatientSymptoms, _, _, _).
activated_rule(_, PatientSymptoms, regla_de_urgencia, Rule) :-
    urgency(PatientSymptoms, _, _, Rule).
activated_rule(Disease, _, medicamento_seguro, opcion_segura_disponible) :-
    disease_medication(Disease, Medication),
    medication_evaluation(Medication, Disease, [], [], [], seguro, seguro, ninguno), !.

