import { useEffect, useMemo, useState } from "react";
import { adminHeaders, apiRequest, apiUrl } from "./api";

const SEVERITIES = ["leve", "moderado", "severo"];

function go(path) {
  window.location.hash = path;
}

function useRoute() {
  const [route, setRoute] = useState(window.location.hash.replace("#", "") || "/");
  useEffect(() => {
    const listener = () => setRoute(window.location.hash.replace("#", "") || "/");
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  return route;
}

function AppShell({ children, catalogs, onNavigate }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => onNavigate("/")} aria-label="Ir al inicio">
          <span className="brand-mark">ML</span>
          <span><strong>Medi</strong>Logic</span>
        </button>
        <nav>
          <button className="nav-link" onClick={() => onNavigate("/paciente")}>Paciente</button>
          <button className="nav-link" onClick={() => onNavigate("/admin")}>Administración</button>
        </nav>
      </header>
      <main>{children}</main>
      <footer className="footer">
        <span>MediLogic · prototipo académico de IA simbólica</span>
        <span>{catalogs ? `${catalogs.symptoms.length} síntomas · catálogo dinámico` : "Cargando catálogo"}</span>
      </footer>
    </div>
  );
}

function Home({ onNavigate }) {
  return (
    <section className="hero page-width">
      <div className="hero-copy">
        <p className="eyebrow">SISTEMA EXPERTO · PROLOG + PYTHON</p>
        <h1>Una primera lectura de tus síntomas, con las reglas a la vista.</h1>
        <p className="lead">MediLogic relaciona síntomas y severidad con una base de conocimiento explicable. Revisa afinidades, urgencia y filtros de seguridad en un solo informe.</p>
        <div className="hero-actions">
          <button className="button primary" onClick={() => onNavigate("/paciente")}>Iniciar análisis</button>
          <button className="button secondary" onClick={() => onNavigate("/admin")}>Entrar como administrador</button>
        </div>
      </div>
      <div className="hero-panel">
        <div className="hero-panel-top"><span className="status-dot" /> Motor lógico activo</div>
        <div className="score-dial"><span>82</span><small>% afinidad</small></div>
        <div className="mini-rule"><span>✓</span> severidad ponderada</div>
        <div className="mini-rule"><span>✓</span> contraindicaciones revisadas</div>
        <div className="mini-rule"><span>✓</span> explicación trazable</div>
      </div>
      <div className="notice full-width"><strong>Importante:</strong> es una herramienta académica de orientación preliminar, no un diagnóstico ni una prescripción. Si tienes síntomas severos o de alarma, busca atención médica inmediata.</div>
    </section>
  );
}

function MultiSelect({ title, items, selected, onChange, emptyText = "No hay registros." }) {
  return (
    <fieldset className="catalog-group">
      <legend>{title}</legend>
      {items.length === 0 && <p className="muted">{emptyText}</p>}
      <div className="check-grid">
        {items.map((item) => (
          <label className="check-card" key={item.id}>
            <input type="checkbox" checked={selected.includes(item.id)} onChange={() => onChange(item.id)} />
            <span><strong>{item.name}</strong><small>{item.description}</small></span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function PatientPage({ catalogs, onNavigate }) {
  const [selectedSymptoms, setSelectedSymptoms] = useState({});
  const [allergies, setAllergies] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [treatments, setTreatments] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const history = useMemo(() => JSON.parse(sessionStorage.getItem("medilogic_history") || "[]"), [result]);

  const toggle = (setter) => (id) => setter((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  const toggleSymptom = (id) => setSelectedSymptoms((current) => {
    if (current[id]) {
      const next = { ...current };
      delete next[id];
      return next;
    }
    return { ...current, [id]: "leve" };
  });

  async function submit(event) {
    event.preventDefault();
    setError("");
    const sintomas = Object.entries(selectedSymptoms).map(([id, severity]) => ({ id, severity }));
    if (!sintomas.length) {
      setError("Selecciona al menos un síntoma para ejecutar el análisis.");
      return;
    }
    setLoading(true);
    try {
      const response = await apiRequest("/api/analisis", { method: "POST", body: JSON.stringify({ sintomas, alergias: allergies, enfermedades_cronicas: conditions, tratamientos_actuales: treatments }) });
      setResult(response);
      const previous = JSON.parse(sessionStorage.getItem("medilogic_history") || "[]");
      sessionStorage.setItem("medilogic_history", JSON.stringify([{ analysis_id: response.analysis_id, created_at: response.created_at, diagnoses: response.diagnoses.slice(0, 3) }, ...previous].slice(0, 10)));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function downloadPdf() {
    const payload = { sintomas: Object.entries(selectedSymptoms).map(([id, severity]) => ({ id, severity })), alergias: allergies, enfermedades_cronicas: conditions, tratamientos_actuales: treatments };
    const response = await fetch(apiUrl("/api/informes/pdf"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (!response.ok) { setError("No se pudo generar el PDF."); return; }
    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "informe-medilogic.pdf";
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <section className="page-width patient-layout">
      <div className="section-heading"><div><p className="eyebrow">MÓDULO DE PACIENTE</p><h2>Cuéntanos cómo te sientes</h2><p className="lead compact">La severidad cambia el peso de cada coincidencia. Marca solo información sintética y revisa el resultado con un profesional.</p></div><span className="pill">{Object.keys(selectedSymptoms).length} síntomas</span></div>
      <form className="patient-form" onSubmit={submit}>
        <fieldset className="catalog-group"><legend>1. Síntomas actuales</legend><div className="symptom-list">{catalogs.symptoms.map((item) => <label className={`symptom-row ${selectedSymptoms[item.id] ? "selected" : ""}`} key={item.id}><input type="checkbox" checked={Boolean(selectedSymptoms[item.id])} onChange={() => toggleSymptom(item.id)} /><span className="symptom-name"><strong>{item.name}</strong><small>{item.alarm ? "Síntoma de alarma" : item.description}</small></span>{selectedSymptoms[item.id] && <select aria-label={`Severidad de ${item.name}`} value={selectedSymptoms[item.id]} onChange={(event) => setSelectedSymptoms((current) => ({ ...current, [item.id]: event.target.value }))}>{SEVERITIES.map((severity) => <option key={severity} value={severity}>{severity[0].toUpperCase() + severity.slice(1)}</option>)}</select>}</label>)}</div></fieldset>
        <div className="form-columns"><MultiSelect title="2. Alergias a medicamentos" items={catalogs.medications} selected={allergies} onChange={toggle(setAllergies)} /><MultiSelect title="3. Enfermedades crónicas / antecedentes" items={catalogs.background_conditions} selected={conditions} onChange={toggle(setConditions)} /></div>
        <MultiSelect title="4. Tratamientos actuales (opcional)" items={catalogs.medications} selected={treatments} onChange={toggle(setTreatments)} />
        {error && <div className="error-box">{error}</div>}
        <div className="form-actions"><button className="button primary" disabled={loading}>{loading ? "Analizando..." : "Ejecutar análisis"}</button><span className="muted">El resultado se conserva temporalmente en esta sesión.</span></div>
      </form>
      {result && <Results result={result} onDownload={downloadPdf} />}
      {history.length > 0 && <section className="history"><div className="section-heading"><div><p className="eyebrow">HISTORIAL TEMPORAL</p><h3>Análisis de esta sesión</h3></div><span className="muted">sessionStorage · no se envía al servidor</span></div><div className="history-grid">{history.map((item) => <div className="history-card" key={item.analysis_id}><small>{new Date(item.created_at).toLocaleString()}</small><strong>{item.diagnoses[0]?.disease_name || "Sin coincidencias"}</strong><span>{item.diagnoses[0] ? `${item.diagnoses[0].affinity}% de afinidad` : "Revisar datos"}</span></div>)}</div></section>}
    </section>
  );
}

function Results({ result, onDownload }) {
  return <section className="results"><div className="section-heading"><div><p className="eyebrow">RESULTADO EXPLICABLE</p><h2>Lo que encontró el motor</h2><p className="muted">Análisis {result.analysis_id} · {new Date(result.created_at).toLocaleString()}</p></div><button className="button secondary" onClick={onDownload}>Descargar PDF</button></div><div className={`urgency ${result.global_urgency.level}`}><span className="urgency-icon">!</span><div><strong>{result.global_urgency.action}</strong><span>Regla activada: {result.global_urgency.rule.replaceAll("_", " ")}</span></div></div>{result.warnings.map((warning) => <div className="notice" key={warning}>{warning}</div>)}<div className="diagnosis-list">{result.diagnoses.length === 0 && <div className="empty-state">No se encontraron coincidencias suficientes en la base de conocimiento.</div>}{result.diagnoses.map((diagnosis, index) => <DiagnosisCard diagnosis={diagnosis} index={index} key={diagnosis.disease_id} />)}</div></section>;
}

function DiagnosisCard({ diagnosis, index }) {
  return <article className="diagnosis-card"><div className="diagnosis-top"><div><span className="rank">0{index + 1}</span><div className="diagnosis-title"><h3>{diagnosis.disease_name}</h3><span>{diagnosis.system} · {diagnosis.type}</span></div></div><div className="affinity"><strong>{diagnosis.affinity}%</strong><small>{diagnosis.points_obtained}/{diagnosis.points_maximum} puntos</small></div></div><div className="affinity-track"><span style={{ width: `${diagnosis.affinity}%` }} /></div><p>{diagnosis.description}</p><div className="result-columns"><div><h4>Coincidencias</h4>{diagnosis.coincidences.map((item) => <div className="line-item" key={item.symptom_id}><span>{item.symptom_name}</span><b>{item.severity} · +{item.weight}</b></div>)}</div><div><h4>Medicamentos</h4>{diagnosis.recommended_medication ? <div className="safe-callout"><strong>{diagnosis.recommended_medication.medication_name}</strong><span>candidato principal seguro</span></div> : <div className="warning-callout">No hay una opción segura registrada.</div>}{diagnosis.safe_medications.length > 0 && <small className="muted">Disponibles: {diagnosis.safe_medications.map((item) => item.medication_name).join(", ")}</small>}{diagnosis.discarded_medications.length > 0 && <details><summary>Ver descartados ({diagnosis.discarded_medications.length})</summary>{diagnosis.discarded_medications.map((item) => <div className="discarded" key={item.medication_id}><strong>{item.medication_name}</strong><span>{item.reason}</span></div>)}</details>}</div></div><details className="rules"><summary>Ver reglas Prolog activadas</summary>{diagnosis.activated_rules.map((item, ruleIndex) => <div key={`${item.rule}-${ruleIndex}`}><strong>{item.rule.replaceAll("_", " ")}</strong><span>{item.explanation}</span></div>)}</details></article>;
}

function LoginPage({ onLogin, onNavigate }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  async function submit(event) { event.preventDefault(); setError(""); try { const response = await apiRequest("/api/auth/login", { method: "POST", body: JSON.stringify(form) }); sessionStorage.setItem("medilogic_admin_token", response.access_token); onLogin(); } catch (requestError) { setError(requestError.message); } }
  return <section className="page-width narrow-page"><div className="login-card"><p className="eyebrow">ACCESO RESTRINGIDO</p><h2>Panel administrativo</h2><p className="lead compact">Gestiona el catálogo que alimenta las reglas de Prolog. Las credenciales se configuran mediante variables de entorno.</p><form onSubmit={submit}><label>Usuario<input required value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></label><label>Contraseña<input required type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label>{error && <div className="error-box">{error}</div>}<button className="button primary">Iniciar sesión</button><button type="button" className="text-button" onClick={() => onNavigate("/")}>Volver al inicio</button></form></div></section>;
}

function AdminPage({ onLogout }) {
  const [knowledge, setKnowledge] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [rpaFile, setRpaFile] = useState(null);
  const [prologSource, setPrologSource] = useState("");
  const [editing, setEditing] = useState({ type: null, id: null });
  const [diseaseForm, setDiseaseForm] = useState({ id: "", name: "", description: "", system: "respiratorio", type: "viral", is_background: false, symptoms: "", medications: "" });
  const [symptomForm, setSymptomForm] = useState({ id: "", name: "", description: "", alarm: false });
  const [medicationForm, setMedicationForm] = useState({ id: "", name: "", description: "" });
  const [conflictForm, setConflictForm] = useState({ medication_id: "", conflict_type: "chronic_condition", reference_id: "", reason: "" });
  const authOptions = { headers: adminHeaders() };
  async function load() { try { setKnowledge(await apiRequest("/api/admin/knowledge", authOptions)); } catch (requestError) { setError(requestError.message); } }
  useEffect(() => { load(); }, []);
  async function change(path, method, body) { setError(""); setMessage(""); try { await apiRequest(path, { method, body: body ? JSON.stringify(body) : undefined, headers: { ...adminHeaders(), ...(body ? { "Content-Type": "application/json" } : {}) } }); setMessage("Cambio guardado y motor Prolog recargado."); await load(); } catch (requestError) { setError(requestError.message); } }
  function diseasePayload() { return { ...diseaseForm, symptoms: diseaseForm.symptoms.split(",").map((item) => item.trim()).filter(Boolean), medications: diseaseForm.medications.split(",").map((item) => item.trim()).filter(Boolean) }; }
  function editRecord(type, item) {
    setEditing({ type, id: item.id });
    if (type === "disease") setDiseaseForm({ ...item, symptoms: item.symptoms.join(","), medications: item.medications.join(",") });
    if (type === "symptom") setSymptomForm(item);
    if (type === "medication") setMedicationForm(item);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function clearEditing() { setEditing({ type: null, id: null }); }
  async function viewProlog() { try { setPrologSource(await apiRequest("/api/admin/prolog", { headers: adminHeaders() })); } catch (requestError) { setError(requestError.message); } }
  async function downloadProlog() { try { const response = await fetch(apiUrl("/api/admin/prolog/download"), { headers: adminHeaders() }); if (!response.ok) throw new Error("No se pudo descargar el archivo Prolog"); const blob = await response.blob(); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "medilogic.pl"; link.click(); URL.revokeObjectURL(link.href); } catch (requestError) { setError(requestError.message); } }
  async function importRpa(event) { event.preventDefault(); if (!rpaFile) return; const data = new FormData(); data.append("file", rpaFile); try { const response = await fetch(apiUrl("/api/admin/rpa/import"), { method: "POST", headers: adminHeaders(), body: data }); if (!response.ok) throw new Error((await response.json()).detail); setMessage("RPA completado: " + JSON.stringify(await response.json())); await load(); } catch (requestError) { setError(requestError.message); } }
  if (!knowledge) return <section className="page-width"><div className="empty-state">Cargando panel...</div></section>;
  const diseaseEditing = editing.type === "disease";
  const symptomEditing = editing.type === "symptom";
  const medicationEditing = editing.type === "medication";
  return <section className="page-width admin-page"><div className="section-heading"><div><p className="eyebrow">MÓDULO ADMINISTRATIVO</p><h2>Base de conocimiento</h2><p className="lead compact">Cada cambio valida relaciones, regenera el archivo .pl, lo recarga y deja una bitácora.</p></div><button className="button secondary" onClick={onLogout}>Cerrar sesión</button></div>{message && <div className="success-box">{message}</div>}{error && <div className="error-box">{error}</div>}<div className="admin-stats"><div><strong>{knowledge.diseases.length}</strong><span>enfermedades</span></div><div><strong>{knowledge.symptoms.length}</strong><span>síntomas</span></div><div><strong>{knowledge.medications.length}</strong><span>medicamentos</span></div><div><strong>{knowledge.contraindications.length}</strong><span>contraindicaciones</span></div></div><div className="admin-grid"><AdminForm title={diseaseEditing ? "Editar enfermedad" : "Nueva enfermedad"} onSubmit={(event) => { event.preventDefault(); change(diseaseEditing ? `/api/admin/enfermedades/${editing.id}` : "/api/admin/enfermedades", diseaseEditing ? "PUT" : "POST", diseasePayload()); }}><input placeholder="id (ej. bronquitis)" required disabled={diseaseEditing} value={diseaseForm.id} onChange={(event) => setDiseaseForm({ ...diseaseForm, id: event.target.value })} /><input placeholder="Nombre" required value={diseaseForm.name} onChange={(event) => setDiseaseForm({ ...diseaseForm, name: event.target.value })} /><textarea placeholder="Descripción" value={diseaseForm.description} onChange={(event) => setDiseaseForm({ ...diseaseForm, description: event.target.value })} /><div className="two-fields"><input placeholder="Sistema" value={diseaseForm.system} onChange={(event) => setDiseaseForm({ ...diseaseForm, system: event.target.value })} /><input placeholder="Tipo" value={diseaseForm.type} onChange={(event) => setDiseaseForm({ ...diseaseForm, type: event.target.value })} /></div><input placeholder="síntomas: tos,fiebre" value={diseaseForm.symptoms} onChange={(event) => setDiseaseForm({ ...diseaseForm, symptoms: event.target.value })} /><input placeholder="medicamentos: paracetamol" value={diseaseForm.medications} onChange={(event) => setDiseaseForm({ ...diseaseForm, medications: event.target.value })} /><label className="inline-check"><input type="checkbox" checked={diseaseForm.is_background} onChange={(event) => setDiseaseForm({ ...diseaseForm, is_background: event.target.checked })} /> Es antecedente / condición crónica</label><button className="button primary">{diseaseEditing ? "Guardar enfermedad" : "Crear enfermedad"}</button>{diseaseEditing && <button type="button" className="text-button" onClick={clearEditing}>Cancelar edición</button>}</AdminForm><AdminForm title={symptomEditing ? "Editar síntoma" : "Nuevo síntoma"} onSubmit={(event) => { event.preventDefault(); change(symptomEditing ? `/api/admin/sintomas/${editing.id}` : "/api/admin/sintomas", symptomEditing ? "PUT" : "POST", symptomForm); }}><input placeholder="id" required disabled={symptomEditing} value={symptomForm.id} onChange={(event) => setSymptomForm({ ...symptomForm, id: event.target.value })} /><input placeholder="Nombre" required value={symptomForm.name} onChange={(event) => setSymptomForm({ ...symptomForm, name: event.target.value })} /><textarea placeholder="Descripción" value={symptomForm.description} onChange={(event) => setSymptomForm({ ...symptomForm, description: event.target.value })} /><label className="inline-check"><input type="checkbox" checked={symptomForm.alarm} onChange={(event) => setSymptomForm({ ...symptomForm, alarm: event.target.checked })} /> Es síntoma de alarma</label><button className="button primary">{symptomEditing ? "Guardar síntoma" : "Crear síntoma"}</button>{symptomEditing && <button type="button" className="text-button" onClick={clearEditing}>Cancelar edición</button>}</AdminForm><AdminForm title={medicationEditing ? "Editar medicamento" : "Nuevo medicamento"} onSubmit={(event) => { event.preventDefault(); change(medicationEditing ? `/api/admin/medicamentos/${editing.id}` : "/api/admin/medicamentos", medicationEditing ? "PUT" : "POST", medicationForm); }}><input placeholder="id" required disabled={medicationEditing} value={medicationForm.id} onChange={(event) => setMedicationForm({ ...medicationForm, id: event.target.value })} /><input placeholder="Nombre" required value={medicationForm.name} onChange={(event) => setMedicationForm({ ...medicationForm, name: event.target.value })} /><textarea placeholder="Descripción" value={medicationForm.description} onChange={(event) => setMedicationForm({ ...medicationForm, description: event.target.value })} /><button className="button primary">{medicationEditing ? "Guardar medicamento" : "Crear medicamento"}</button>{medicationEditing && <button type="button" className="text-button" onClick={clearEditing}>Cancelar edición</button>}</AdminForm><AdminForm title="Nueva contraindicación" onSubmit={(event) => { event.preventDefault(); change("/api/admin/contraindicaciones", "POST", conflictForm); }}><select required value={conflictForm.medication_id} onChange={(event) => setConflictForm({ ...conflictForm, medication_id: event.target.value })}><option value="">Medicamento</option>{knowledge.medications.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select value={conflictForm.conflict_type} onChange={(event) => setConflictForm({ ...conflictForm, conflict_type: event.target.value })}><option value="chronic_condition">Condición crónica</option><option value="disease">Enfermedad</option><option value="treatment">Tratamiento</option></select><input required placeholder="id de referencia" value={conflictForm.reference_id} onChange={(event) => setConflictForm({ ...conflictForm, reference_id: event.target.value })} /><textarea required placeholder="Motivo" value={conflictForm.reason} onChange={(event) => setConflictForm({ ...conflictForm, reason: event.target.value })} /><button className="button primary">Crear contraindicación</button></AdminForm></div><section className="admin-section"><div className="section-heading"><div><h3>Registros actuales</h3><p className="muted">Edita o elimina registros; las relaciones inválidas son rechazadas.</p></div><div className="hero-actions"><button className="button secondary" onClick={viewProlog}>Ver .pl</button><button className="button secondary" onClick={downloadProlog}>Descargar .pl</button></div></div>{prologSource && <pre className="prolog-preview">{prologSource}</pre>}<div className="record-columns"><RecordList title="Enfermedades" items={knowledge.diseases} onEdit={(item) => editRecord("disease", item)} onDelete={(item) => change(`/api/admin/enfermedades/${item.id}`, "DELETE")} /><RecordList title="Síntomas" items={knowledge.symptoms} onEdit={(item) => editRecord("symptom", item)} onDelete={(item) => change(`/api/admin/sintomas/${item.id}`, "DELETE")} /><RecordList title="Medicamentos" items={knowledge.medications} onEdit={(item) => editRecord("medication", item)} onDelete={(item) => change(`/api/admin/medicamentos/${item.id}`, "DELETE")} /></div><div className="record-list contraindication-list"><h4>Contraindicaciones</h4>{knowledge.contraindications.map((item) => <div className="record-row" key={`${item.medication_id}-${item.conflict_type}-${item.reference_id}`}><span><strong>{item.medication_id} / {item.reference_id}</strong><small>{item.conflict_type}: {item.reason}</small></span><button className="icon-button" onClick={() => change(`/api/admin/contraindicaciones/${item.medication_id}/${item.conflict_type}/${item.reference_id}`, "DELETE")}>×</button></div>)}</div></section><section className="admin-section rpa-box"><div><p className="eyebrow">AUTOMATIZACIÓN ROBÓTICA</p><h3>Cargar enfermedades desde TXT</h3><p className="muted">El adaptador actual recibe JSON UTF-8 dentro de un archivo .txt y registra la operación en logs/rpa_*.txt.</p></div><form onSubmit={importRpa} className="rpa-form"><input type="file" accept=".txt" onChange={(event) => setRpaFile(event.target.files[0])} required /><button className="button primary">Ejecutar RPA</button></form></section></section>;
}

function AdminForm({ title, children, onSubmit }) { return <form className="admin-form" onSubmit={onSubmit}><h3>{title}</h3>{children}</form>; }
function RecordList({ title, items, onEdit, onDelete }) { return <div className="record-list"><h4>{title}</h4>{items.map((item) => <div className="record-row" key={item.id}><span><strong>{item.name}</strong><small>{item.id}</small></span><div className="record-actions">{onEdit && <button className="small-button" onClick={() => onEdit(item)}>Editar</button>}<button className="icon-button" title={`Eliminar ${item.name}`} onClick={() => onDelete(item)}>×</button></div></div>)}</div>; }

export default function App() {
  const route = useRoute();
  const [catalogs, setCatalogs] = useState(null);
  const [catalogError, setCatalogError] = useState("");
  const [adminLogged, setAdminLogged] = useState(Boolean(sessionStorage.getItem("medilogic_admin_token")));
  useEffect(() => { apiRequest("/api/catalogos").then(setCatalogs).catch((error) => setCatalogError(error.message)); }, []);
  function logout() { const token = sessionStorage.getItem("medilogic_admin_token"); sessionStorage.removeItem("medilogic_admin_token"); setAdminLogged(false); apiRequest("/api/auth/logout", { method: "POST", headers: { Authorization: `Bearer ${token}` } }).catch(() => {}); go("/"); }
  let content;
  if (catalogError) content = <section className="page-width"><div className="error-box">No se pudo cargar el catálogo: {catalogError}. Verifica que FastAPI esté ejecutándose.</div></section>;
  else if (!catalogs) content = <section className="page-width"><div className="empty-state">Conectando con el motor lógico...</div></section>;
  else if (route === "/paciente") content = <PatientPage catalogs={catalogs} onNavigate={go} />;
  else if (route === "/admin" && !adminLogged) content = <LoginPage onLogin={() => setAdminLogged(true)} onNavigate={go} />;
  else if (route === "/admin") content = <AdminPage onLogout={logout} />;
  else content = <Home onNavigate={go} />;
  return <AppShell catalogs={catalogs} onNavigate={go}>{content}</AppShell>;
}
