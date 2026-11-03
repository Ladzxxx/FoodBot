from localization import t

# CAN CHANGE TEXT: вопросы, стабильные коды и подписи описания одного эпизода.
PAIN_QUESTIONS = {
    'pain_location': t("en", 'pain.question.pain_location'),
    'pain_character': t("en", 'pain.question.pain_character'),
    'pain_symptoms': t("en", 'pain.question.pain_symptoms'),
    'pain_triggers': t("en", 'pain.question.pain_triggers'),
}
PAIN_OPTIONS = {
    'pain_location': [
        ('upper_right', 'Upper right'), ('upper_middle', 'Upper middle'), ('upper_left', 'Upper left'),
        ('middle_right', 'Middle right'), ('navel', 'Around navel'), ('middle_left', 'Middle left'),
        ('lower_right', 'Lower right'), ('lower_middle', 'Lower middle'), ('lower_left', 'Lower left'),
        ('all_over', 'All over the abdomen'), ('other', 'Other area'),
    ],
    'pain_character': [
        ('cramping', 'Cramping'), ('sharp', 'Sharp/stabbing'), ('dull', 'Dull/aching'),
        ('burning', 'Burning'), ('pressure', 'Pressure'), ('throbbing', 'Throbbing'), ('other', 'Other'),
    ],
    'pain_symptoms': [
        ('bloating', 'Bloating'), ('nausea', 'Nausea'), ('vomiting', 'Vomiting'),
        ('diarrhoea', 'Diarrhoea'), ('constipation', 'Constipation'), ('heartburn', 'Heartburn'),
        ('feverish', 'Fever / felt feverish'), ('fainting', 'Fainting'),
        ('blood_vomit', 'Blood in vomit'), ('black_stool', 'Black, sticky stool'),
        ('bowel_bleeding', 'Heavy bleeding from the bowel'), ('breathing', 'Trouble breathing'), ('other', 'Other'),
    ],
    'pain_triggers': [
        ('food', 'Particular food or drink'), ('large_meal', 'Larger meal than usual'),
        ('meal_gap', 'Long gap between meals'), ('late_eating', 'Eating late'),
        ('stress', 'Stress or anxiety'), ('sleep', 'Poor or short sleep'),
        ('activity', 'Physical activity'), ('medicine', 'Medicine or supplement'), ('other', 'Other'),
    ],
}
URGENT_CODES = {'fainting', 'blood_vomit', 'black_stool', 'bowel_bleeding', 'breathing'}


def option_labels(key, lang="en"):
    labels = {code: t(lang, "pain.option." + key + "." + code) for code, original in PAIN_OPTIONS[key]}
    labels.update({"none": t(lang, "common.none"), "unknown": t(lang, "common.not_sure"), "skipped": t(lang, "common.skip")})
    if key == 'pain_triggers':
        # CAN CHANGE TEXT
        labels['none'] = t(lang, 'pain.no_clear_trigger')
    if key not in ('pain_symptoms', 'pain_triggers'):
        labels.pop('none')
    return labels


def selected_labels(key, options, lang="en"):
    labels = option_labels(key, lang=lang)
    result = []
    for option in options:
        if option['is_selected']:
            text = labels[option['option_code']]
            if option['custom_text']:
                text += ': ' + option['custom_text']
            result.append(text)
    return result


def next_pain_question(key):
    keys = list(PAIN_QUESTIONS)
    index = keys.index(key) + 1
    return keys[index] if index < len(keys) else 'pain_comment_wanted'
