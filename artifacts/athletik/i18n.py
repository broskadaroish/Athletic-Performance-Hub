"""
Bruce Football Performance Diagnostics — Mehrsprachigkeit
Unterstützte Sprachen: Deutsch (de) / Englisch (en)
Verwendung:  from i18n import t, SPRACHEN
             t("speichern")  → "Speichern" / "Save"
"""
import streamlit as st

SPRACHEN = {
    "de": "🇩🇪 Deutsch",
    "en": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 English",
    "tr": "🇹🇷 Türkçe",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "pt": "🇵🇹 Português",
    "ru": "🇷🇺 Русский",
}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Navigation ────────────────────────────────────────────────────────────
    "nav_startseite":    {"de": "🏠  Startseite",   "en": "🏠  Dashboard",   "tr": "🏠  Ana Sayfa",   "es": "🏠  Inicio",       "fr": "🏠  Accueil",      "pt": "🏠  Início",       "ru": "🏠  Главная"},
    "nav_spieler":       {"de": "👤  Spieler",       "en": "👤  Players",     "tr": "👤  Oyuncular",   "es": "👤  Jugadores",    "fr": "👤  Joueurs",      "pt": "👤  Jogadores",    "ru": "👤  Игроки"},
    "nav_diagnostik":    {"de": "🔬  Diagnostik",    "en": "🔬  Diagnostics", "tr": "🔬  Tanı",        "es": "🔬  Diagnóstico",  "fr": "🔬  Diagnostic",   "pt": "🔬  Diagnóstico",  "ru": "🔬  Диагностика"},
    "nav_training":      {"de": "📅  Training",      "en": "📅  Training",    "tr": "📅  Antrenman",   "es": "📅  Entrenamiento","fr": "📅  Entraînement", "pt": "📅  Treino",       "ru": "📅  Тренировка"},
    "nav_entwicklung":   {"de": "📈  Entwicklung",   "en": "📈  Development", "tr": "📈  Gelişim",     "es": "📈  Desarrollo",   "fr": "📈  Développement","pt": "📈  Desenvolvimento","ru": "📈  Развитие"},
    "nav_vergleich":     {"de": "⚖️  Vergleich",     "en": "⚖️  Comparison",  "tr": "⚖️  Karşılaştır","es": "⚖️  Comparación", "fr": "⚖️  Comparaison",  "pt": "⚖️  Comparação",   "ru": "⚖️  Сравнение"},
    "nav_mannschaft":    {"de": "👥  Mannschaft",    "en": "👥  Team",        "tr": "👥  Takım",       "es": "👥  Equipo",       "fr": "👥  Équipe",       "pt": "👥  Equipa",       "ru": "👥  Команда"},
    "nav_protokoll":     {"de": "🖨️  Protokoll",     "en": "🖨️  Protocol",    "tr": "🖨️  Protokol",   "es": "🖨️  Protocolo",   "fr": "🖨️  Protocole",    "pt": "🖨️  Protocolo",    "ru": "🖨️  Протокол"},
    "nav_anleitungen":   {"de": "📄  Anleitungen",   "en": "📄  Instructions","tr": "📄  Talimatlar",  "es": "📄  Instrucciones","fr": "📄  Instructions",  "pt": "📄  Instruções",   "ru": "📄  Инструкции"},
    "nav_einstellungen": {"de": "⚙️  Einstellungen", "en": "⚙️  Settings",    "tr": "⚙️  Ayarlar",    "es": "⚙️  Ajustes",     "fr": "⚙️  Paramètres",   "pt": "⚙️  Definições",   "ru": "⚙️  Настройки"},
    "nav_ueber":         {"de": "ℹ️  Über",           "en": "ℹ️  About",       "tr": "ℹ️  Hakkında",   "es": "ℹ️  Acerca de",   "fr": "ℹ️  À propos",     "pt": "ℹ️  Sobre",        "ru": "ℹ️  О программе"},

    # ── Spieler-Sub-Navigation ────────────────────────────────────────────────
    "sub_verwaltung":    {"de": "👥 Verwaltung",          "en": "👥 Management",        "tr": "👥 Yönetim",         "es": "👥 Gestión",          "fr": "👥 Gestion",           "pt": "👥 Gestão",           "ru": "👥 Управление"},
    "sub_profil":        {"de": "🏃 Profil & Diagnostik", "en": "🏃 Profile & Diagnostics","tr": "🏃 Profil & Tanı", "es": "🏃 Perfil & Diagnóstico","fr": "🏃 Profil & Diagnostic","pt": "🏃 Perfil & Diagnóstico","ru": "🏃 Профиль & Диагностика"},
    "sub_anthropometrie":{"de": "📐 Anthropometrie",      "en": "📐 Anthropometry",      "tr": "📐 Antropometri",    "es": "📐 Antropometría",     "fr": "📐 Anthropométrie",    "pt": "📐 Antropometria",    "ru": "📐 Антропометрия"},

    # ── Diagnostik-Sub-Navigation ─────────────────────────────────────────────
    "sub_diag_overview": {"de": "🏠 Übersicht",  "en": "🏠 Overview",  "tr": "🏠 Genel Bakış","es": "🏠 Resumen",    "fr": "🏠 Aperçu",    "pt": "🏠 Visão Geral","ru": "🏠 Обзор"},
    "sub_fms":           {"de": "📝 FMS",         "en": "📝 FMS",       "tr": "📝 FMS",        "es": "📝 FMS",        "fr": "📝 FMS",        "pt": "📝 FMS",        "ru": "📝 FMS"},
    "sub_ybalance":      {"de": "📏 Y-Balance",   "en": "📏 Y-Balance", "tr": "📏 Y-Denge",    "es": "📏 Y-Balance",  "fr": "📏 Y-Balance",  "pt": "📏 Y-Balance",  "ru": "📏 Y-Баланс"},
    "sub_sprint":        {"de": "⚡ Sprint",       "en": "⚡ Sprint",    "tr": "⚡ Sprint",     "es": "⚡ Sprint",     "fr": "⚡ Sprint",     "pt": "⚡ Sprint",     "ru": "⚡ Спринт"},
    "sub_sprung":        {"de": "🦘 Sprung",       "en": "🦘 Jump",      "tr": "🦘 Zıplama",    "es": "🦘 Salto",      "fr": "🦘 Saut",       "pt": "🦘 Salto",      "ru": "🦘 Прыжок"},
    "sub_agilitaet":     {"de": "🔀 Agilität",    "en": "🔀 Agility",   "tr": "🔀 Çeviklik",   "es": "🔀 Agilidad",   "fr": "🔀 Agilité",    "pt": "🔀 Agilidade",  "ru": "🔀 Ловкость"},
    "sub_ausdauer":      {"de": "🫁 Ausdauer",    "en": "🫁 Endurance", "tr": "🫁 Dayanıklılık","es": "🫁 Resistencia","fr": "🫁 Endurance",  "pt": "🫁 Resistência","ru": "🫁 Выносливость"},
    "sub_kraft":         {"de": "💪 Kraft",        "en": "💪 Strength",  "tr": "💪 Güç",        "es": "💪 Fuerza",     "fr": "💪 Force",      "pt": "💪 Força",      "ru": "💪 Сила"},

    # ── Training-Sub-Navigation ───────────────────────────────────────────────
    "sub_trainingsplan": {"de": "📅 Trainingsplan",   "en": "📅 Training Plan",    "tr": "📅 Antrenman Planı","es": "📅 Plan de Entreno","fr": "📅 Plan d'entraînement","pt": "📅 Plano de Treino","ru": "📅 План тренировок"},
    "sub_periodisierung":{"de": "🔄 Periodisierung",  "en": "🔄 Periodisation",    "tr": "🔄 Periyodizasyon", "es": "🔄 Periodización",  "fr": "🔄 Périodisation",     "pt": "🔄 Periodização",  "ru": "🔄 Периодизация"},

    # ── Allgemeine Buttons ────────────────────────────────────────────────────
    "speichern":         {"de": "💾 Speichern",     "en": "💾 Save",      "tr": "💾 Kaydet",      "es": "💾 Guardar",    "fr": "💾 Enregistrer", "pt": "💾 Guardar",    "ru": "💾 Сохранить"},
    "loeschen":          {"de": "🗑️ Löschen",       "en": "🗑️ Delete",    "tr": "🗑️ Sil",         "es": "🗑️ Eliminar",   "fr": "🗑️ Supprimer",   "pt": "🗑️ Apagar",     "ru": "🗑️ Удалить"},
    "abbrechen":         {"de": "Abbrechen",         "en": "Cancel",       "tr": "İptal",          "es": "Cancelar",      "fr": "Annuler",        "pt": "Cancelar",      "ru": "Отмена"},
    "zurueck":           {"de": "← Zurück",          "en": "← Back",       "tr": "← Geri",         "es": "← Atrás",       "fr": "← Retour",       "pt": "← Voltar",      "ru": "← Назад"},
    "generieren":        {"de": "⚡ Generieren",     "en": "⚡ Generate",  "tr": "⚡ Oluştur",     "es": "⚡ Generar",    "fr": "⚡ Générer",     "pt": "⚡ Gerar",      "ru": "⚡ Создать"},
    "herunterladen":     {"de": "⬇ Herunterladen",  "en": "⬇ Download",  "tr": "⬇ İndir",        "es": "⬇ Descargar",  "fr": "⬇ Télécharger",  "pt": "⬇ Descarregar","ru": "⬇ Скачать"},
    "exportieren":       {"de": "📤 Exportieren",    "en": "📤 Export",    "tr": "📤 Dışa Aktar",  "es": "📤 Exportar",   "fr": "📤 Exporter",    "pt": "📤 Exportar",   "ru": "📤 Экспорт"},
    "aktualisieren":     {"de": "🔄 Aktualisieren",  "en": "🔄 Refresh",   "tr": "🔄 Yenile",      "es": "🔄 Actualizar", "fr": "🔄 Actualiser",  "pt": "🔄 Atualizar",  "ru": "🔄 Обновить"},
    "hinzufuegen":       {"de": "➕ Hinzufügen",     "en": "➕ Add",       "tr": "➕ Ekle",         "es": "➕ Añadir",     "fr": "➕ Ajouter",     "pt": "➕ Adicionar",  "ru": "➕ Добавить"},
    "bearbeiten":        {"de": "✏️ Bearbeiten",     "en": "✏️ Edit",      "tr": "✏️ Düzenle",     "es": "✏️ Editar",     "fr": "✏️ Modifier",    "pt": "✏️ Editar",     "ru": "✏️ Изменить"},
    "bestaetigen":       {"de": "✅ Bestätigen",     "en": "✅ Confirm",   "tr": "✅ Onayla",      "es": "✅ Confirmar",  "fr": "✅ Confirmer",   "pt": "✅ Confirmar",  "ru": "✅ Подтвердить"},

    # ── Spielerverwaltung ─────────────────────────────────────────────────────
    "spieler_neu":       {"de": "➕ Neu anlegen",    "en": "➕ New Player", "tr": "➕ Yeni Oyuncu", "es": "➕ Nuevo Jugador","fr": "➕ Nouveau Joueur","pt": "➕ Novo Jogador","ru": "➕ Новый игрок"},
    "spieler_bearbeiten":{"de": "✏️ Bearbeiten",     "en": "✏️ Edit",      "tr": "✏️ Düzenle",     "es": "✏️ Editar",     "fr": "✏️ Modifier",    "pt": "✏️ Editar",     "ru": "✏️ Изменить"},
    "spieler_alle":      {"de": "📋 Alle Spieler",   "en": "📋 All Players","tr": "📋 Tüm Oyuncular","es": "📋 Todos los Jugadores","fr": "📋 Tous les Joueurs","pt": "📋 Todos os Jogadores","ru": "📋 Все игроки"},
    "vorname":           {"de": "Vorname",            "en": "First Name",   "tr": "Ad",             "es": "Nombre",        "fr": "Prénom",         "pt": "Nome",          "ru": "Имя"},
    "nachname":          {"de": "Nachname",           "en": "Last Name",    "tr": "Soyad",          "es": "Apellido",      "fr": "Nom de famille", "pt": "Apelido",       "ru": "Фамилия"},
    "geburtsdatum":      {"de": "Geburtsdatum (TT.MM.JJJJ)", "en": "Date of Birth (DD.MM.YYYY)", "tr": "Doğum Tarihi (GG.AA.YYYY)", "es": "Fecha de Nacimiento (DD.MM.AAAA)", "fr": "Date de Naissance (JJ.MM.AAAA)", "pt": "Data de Nascimento (DD.MM.AAAA)", "ru": "Дата рождения (ДД.ММ.ГГГГ)"},
    "geschlecht":        {"de": "Geschlecht",         "en": "Gender",       "tr": "Cinsiyet",       "es": "Sexo",          "fr": "Genre",          "pt": "Género",        "ru": "Пол"},
    "maennlich":         {"de": "Männlich",           "en": "Male",         "tr": "Erkek",          "es": "Masculino",     "fr": "Masculin",       "pt": "Masculino",     "ru": "Мужской"},
    "weiblich":          {"de": "Weiblich",           "en": "Female",       "tr": "Kadın",          "es": "Femenino",      "fr": "Féminin",        "pt": "Feminino",      "ru": "Женский"},
    "divers":            {"de": "Divers",             "en": "Other",        "tr": "Diğer",          "es": "Otro",          "fr": "Autre",          "pt": "Outro",         "ru": "Другое"},
    "altersklasse":      {"de": "Altersklasse",       "en": "Age Group",    "tr": "Yaş Grubu",      "es": "Categoría",     "fr": "Catégorie d'âge","pt": "Escalão",       "ru": "Возрастная группа"},
    "hauptposition":     {"de": "Hauptposition",      "en": "Main Position","tr": "Ana Pozisyon",   "es": "Posición Principal","fr": "Position Principale","pt": "Posição Principal","ru": "Основная позиция"},
    "nebenposition":     {"de": "Nebenposition",      "en": "Secondary Position","tr": "Yan Pozisyon","es": "Posición Secundaria","fr": "Position Secondaire","pt": "Posição Secundária","ru": "Дополнительная позиция"},
    "spielbein":         {"de": "Spielbein",          "en": "Preferred Foot","tr": "Tercih Edilen Ayak","es": "Pie Dominante","fr": "Pied Préféré",  "pt": "Pé Dominante",  "ru": "Рабочая нога"},
    "leistungsniveau":   {"de": "Leistungsniveau",    "en": "Performance Level","tr": "Performans Seviyesi","es": "Nivel de Rendimiento","fr": "Niveau de Performance","pt": "Nível de Desempenho","ru": "Уровень мастерства"},
    "mannschaft":        {"de": "Mannschaft / Verein","en": "Team / Club",  "tr": "Takım / Kulüp", "es": "Equipo / Club", "fr": "Équipe / Club",  "pt": "Equipa / Clube","ru": "Команда / Клуб"},
    "trainingsstatus":   {"de": "Trainingsstatus",    "en": "Training Status","tr": "Antrenman Durumu","es": "Estado de Entrenamiento","fr": "Statut d'Entraînement","pt": "Estado de Treino","ru": "Статус тренировки"},

    # ── Einstellungen ─────────────────────────────────────────────────────────
    "einst_allgemein":   {"de": "⚙️ Allgemein",        "en": "⚙️ General",     "tr": "⚙️ Genel",         "es": "⚙️ General",       "fr": "⚙️ Général",       "pt": "⚙️ Geral",         "ru": "⚙️ Общее"},
    "einst_zweck":       {"de": "📋 Zweckbestimmung",  "en": "📋 Purpose",      "tr": "📋 Amaç",          "es": "📋 Propósito",      "fr": "📋 Objectif",       "pt": "📋 Propósito",      "ru": "📋 Назначение"},
    "einst_checklisten": {"de": "✅ Checklisten",      "en": "✅ Checklists",   "tr": "✅ Kontrol Listesi","es": "✅ Listas de control","fr": "✅ Listes de contrôle","pt": "✅ Listas de verificação","ru": "✅ Контрольные списки"},
    "einst_export":      {"de": "💾 Export & Backup",  "en": "💾 Export & Backup","tr": "💾 Dışa Aktar & Yedek","es": "💾 Exportar & Copia","fr": "💾 Export & Sauvegarde","pt": "💾 Exportar & Backup","ru": "💾 Экспорт & Резерв"},
    "einst_datenschutz": {"de": "🔒 Datenschutz",     "en": "🔒 Privacy",      "tr": "🔒 Gizlilik",      "es": "🔒 Privacidad",     "fr": "🔒 Confidentialité","pt": "🔒 Privacidade",    "ru": "🔒 Конфиденциальность"},
    "einst_sprache":     {"de": "🌐 Sprache",          "en": "🌐 Language",     "tr": "🌐 Dil",           "es": "🌐 Idioma",         "fr": "🌐 Langue",         "pt": "🌐 Idioma",         "ru": "🌐 Язык"},
    "vereinsname":       {"de": "Vereinsname",         "en": "Club Name",       "tr": "Kulüp Adı",        "es": "Nombre del Club",   "fr": "Nom du Club",       "pt": "Nome do Clube",     "ru": "Название клуба"},
    "saison":            {"de": "Aktuelle Saison",     "en": "Current Season",  "tr": "Mevcut Sezon",     "es": "Temporada Actual",  "fr": "Saison Actuelle",   "pt": "Época Atual",       "ru": "Текущий сезон"},

    # ── Testprotokoll ─────────────────────────────────────────────────────────
    "spieler":           {"de": "Spieler",       "en": "Player",    "tr": "Oyuncu",      "es": "Jugador",   "fr": "Joueur",     "pt": "Jogador",   "ru": "Игрок"},
    "datum":             {"de": "Datum",          "en": "Date",      "tr": "Tarih",       "es": "Fecha",     "fr": "Date",       "pt": "Data",      "ru": "Дата"},
    "ergebnis":          {"de": "Ergebnis",       "en": "Result",    "tr": "Sonuç",       "es": "Resultado", "fr": "Résultat",   "pt": "Resultado", "ru": "Результат"},
    "bewertung":         {"de": "Bewertung",      "en": "Rating",    "tr": "Değerlendirme","es": "Valoración","fr": "Évaluation", "pt": "Avaliação", "ru": "Оценка"},
    "bemerkung":         {"de": "Bemerkung",      "en": "Notes",     "tr": "Not",         "es": "Notas",     "fr": "Remarques",  "pt": "Notas",     "ru": "Примечания"},
    "alter":             {"de": "Alter",          "en": "Age",       "tr": "Yaş",         "es": "Edad",      "fr": "Âge",        "pt": "Idade",     "ru": "Возраст"},
    "test":              {"de": "Test",           "en": "Test",      "tr": "Test",        "es": "Test",      "fr": "Test",       "pt": "Teste",     "ru": "Тест"},
    "woche":             {"de": "Woche",          "en": "Week",      "tr": "Hafta",       "es": "Semana",    "fr": "Semaine",    "pt": "Semana",    "ru": "Неделя"},
    "phase":             {"de": "Phase",          "en": "Phase",     "tr": "Faz",         "es": "Fase",      "fr": "Phase",      "pt": "Fase",      "ru": "Фаза"},
    "pause":             {"de": "Pause",          "en": "Rest",      "tr": "Mola",        "es": "Pausa",     "fr": "Repos",      "pt": "Pausa",     "ru": "Пауза"},
    "saetze":            {"de": "Sätze",          "en": "Sets",      "tr": "Set",         "es": "Series",    "fr": "Séries",     "pt": "Séries",    "ru": "Подходы"},
    "wiederholungen":    {"de": "Wiederholungen", "en": "Reps",      "tr": "Tekrar",      "es": "Reps",      "fr": "Rép.",       "pt": "Reps",      "ru": "Повторения"},
    "uebung":            {"de": "Übung",          "en": "Exercise",  "tr": "Egzersiz",    "es": "Ejercicio", "fr": "Exercice",   "pt": "Exercício", "ru": "Упражнение"},
    "bereich":           {"de": "Bereich",        "en": "Area",      "tr": "Alan",        "es": "Área",      "fr": "Zone",       "pt": "Área",      "ru": "Область"},

    # ── Checklisten-UI ────────────────────────────────────────────────────────
    "chk_eigene_punkte":    {"de": "Eigene Punkte pro Test",         "en": "Custom Checklist Points",  "tr": "Özel Kontrol Noktaları",     "es": "Puntos personalizados",     "fr": "Points personnalisés",      "pt": "Pontos personalizados",     "ru": "Свои пункты"},
    "chk_standard_default": {"de": "Standard-Checkliste (alle Tests)","en": "Default Checklist (all tests)","tr": "Standart Kontrol Listesi",  "es": "Lista estándar (todos)",    "fr": "Liste standard (tous)",     "pt": "Lista padrão (todos)",      "ru": "Стандартный список"},
    "chk_kein_coaching":    {"de": "Kein Coaching — nur beobachten", "en": "No coaching — observe only","tr": "Antrenman yok — sadece gözlem","es": "Sin coaching — solo observar","fr": "Pas de coaching — observer", "pt": "Sem coaching — só observar","ru": "Без коучинга — только наблюдение"},
    "chk_abbruch_erklaert": {"de": "Abbruchsignal erklärt",          "en": "Stop signal explained",    "tr": "Durdurma sinyali açıklandı", "es": "Señal de parada explicada", "fr": "Signal d'arrêt expliqué",   "pt": "Sinal de paragem explicado","ru": "Сигнал остановки объяснён"},

    # ── Status / Ampel ────────────────────────────────────────────────────────
    "sehr_gut":          {"de": "Sehr gut",            "en": "Excellent",     "tr": "Çok iyi",        "es": "Excelente",     "fr": "Excellent",      "pt": "Excelente",     "ru": "Отлично"},
    "gut":               {"de": "Gut",                 "en": "Good",          "tr": "İyi",            "es": "Bueno",         "fr": "Bon",            "pt": "Bom",           "ru": "Хорошо"},
    "mittel":            {"de": "Mittel",              "en": "Average",       "tr": "Orta",           "es": "Promedio",      "fr": "Moyen",          "pt": "Médio",         "ru": "Средне"},
    "verbesserung":      {"de": "Verbesserungsbedarf", "en": "Needs improvement","tr": "Geliştirilmeli","es": "Mejorable",   "fr": "À améliorer",    "pt": "A melhorar",    "ru": "Требует улучшения"},
    "handlungsbedarf":   {"de": "Handlungsbedarf",     "en": "Action required","tr": "Önlem gerekli", "es": "Acción requerida","fr": "Action requise","pt": "Ação necessária","ru": "Требуются меры"},
    "kein_test":         {"de": "Kein Test",           "en": "Not tested",    "tr": "Test yok",       "es": "Sin test",      "fr": "Non testé",      "pt": "Sem teste",     "ru": "Не тестировался"},

    # ── Trainingsplan ─────────────────────────────────────────────────────────
    "plan_erstellen":    {"de": "⚡ Trainingsplan erstellen","en": "⚡ Generate Training Plan","tr": "⚡ Plan Oluştur","es": "⚡ Crear Plan","fr": "⚡ Créer le Plan","pt": "⚡ Criar Plano","ru": "⚡ Создать план"},
    "plan_laenge":       {"de": "Planlänge",     "en": "Plan Duration", "tr": "Plan Süresi",    "es": "Duración del plan","fr": "Durée du plan",  "pt": "Duração do plano","ru": "Длительность плана"},
    "wochen":            {"de": "Wochen",        "en": "Weeks",         "tr": "Hafta",          "es": "Semanas",          "fr": "Semaines",        "pt": "Semanas",         "ru": "Недели"},
    "haeufigkeit":       {"de": "Häufigkeit",    "en": "Frequency",     "tr": "Sıklık",         "es": "Frecuencia",       "fr": "Fréquence",       "pt": "Frequência",      "ru": "Частота"},
    "ausfuehrung":       {"de": "Ausführung",    "en": "Execution",     "tr": "Uygulama",       "es": "Ejecución",        "fr": "Exécution",       "pt": "Execução",        "ru": "Выполнение"},

    # ── Über die Software ─────────────────────────────────────────────────────
    "ueber_software":    {"de": "Software",      "en": "Software",      "tr": "Yazılım",        "es": "Software",      "fr": "Logiciel",       "pt": "Software",      "ru": "Программа"},
    "ueber_entwickler":  {"de": "Entwickler",    "en": "Developer",     "tr": "Geliştirici",    "es": "Desarrollador", "fr": "Développeur",    "pt": "Desenvolvedor", "ru": "Разработчик"},
    "ueber_kontakt":     {"de": "Kontakt",       "en": "Contact",       "tr": "İletişim",       "es": "Contacto",      "fr": "Contact",        "pt": "Contacto",      "ru": "Контакт"},
    "ueber_copyright":   {"de": "Copyright",     "en": "Copyright",     "tr": "Telif Hakkı",    "es": "Derechos",      "fr": "Droits",         "pt": "Direitos",      "ru": "Авторские права"},
    "ueber_kontaktieren":{"de": "📧 Entwickler kontaktieren","en": "📧 Contact Developer","tr": "📧 Geliştiriciyle İletişim","es": "📧 Contactar Desarrollador","fr": "📧 Contacter le Développeur","pt": "📧 Contactar Desenvolvedor","ru": "📧 Связаться с разработчиком"},
    "urheberrecht":      {"de": "⚖️ Urheberrecht","en": "⚖️ Copyright Notice","tr": "⚖️ Telif Hakkı","es": "⚖️ Aviso Legal","fr": "⚖️ Mention légale","pt": "⚖️ Aviso Legal","ru": "⚖️ Авторское право"},
    "version":           {"de": "Version",       "en": "Version",       "tr": "Sürüm",          "es": "Versión",       "fr": "Version",        "pt": "Versão",        "ru": "Версия"},

    # ── Fehler / Hinweise ─────────────────────────────────────────────────────
    "kein_spieler":      {"de": "Kein Spieler ausgewählt.",    "en": "No player selected.",    "tr": "Oyuncu seçilmedi.",     "es": "Ningún jugador seleccionado.","fr": "Aucun joueur sélectionné.","pt": "Nenhum jogador selecionado.","ru": "Игрок не выбран."},
    "keine_daten":       {"de": "Noch keine Daten vorhanden.", "en": "No data available yet.", "tr": "Henüz veri yok.",       "es": "Sin datos disponibles.",      "fr": "Pas encore de données.",    "pt": "Sem dados disponíveis.",     "ru": "Данных пока нет."},
    "gespeichert":       {"de": "✅ Gespeichert.",             "en": "✅ Saved.",               "tr": "✅ Kaydedildi.",        "es": "✅ Guardado.",                "fr": "✅ Enregistré.",             "pt": "✅ Guardado.",                "ru": "✅ Сохранено."},
    "fehler":            {"de": "❌ Fehler:",                  "en": "❌ Error:",               "tr": "❌ Hata:",              "es": "❌ Error:",                   "fr": "❌ Erreur :",                "pt": "❌ Erro:",                    "ru": "❌ Ошибка:"},
}


def t(key: str) -> str:
    """Gibt den übersetzten Text für den aktuellen Sprachcode zurück.
    Falls der Schlüssel nicht gefunden wird, wird der Schlüssel selbst zurückgegeben."""
    lang = st.session_state.get("lang", "de")
    entry = _TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get("de", key))


def get_lang() -> str:
    """Gibt den aktuellen Sprachcode zurück."""
    return st.session_state.get("lang", "de")


def set_lang(lang_code: str) -> None:
    """Setzt die aktive Sprache."""
    if lang_code in SPRACHEN:
        st.session_state["lang"] = lang_code
