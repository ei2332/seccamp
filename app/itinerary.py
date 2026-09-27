"""旅程の入力検証。表示順は日・時刻・入力順。"""
import re


def read_steps(form):
    keys = ('day', 'time', 'title', 'place', 'note')
    columns = [form.getlist('step_' + key) for key in keys]
    if len({len(column) for column in columns}) != 1 or len(columns[0]) > 50:
        return [], '予定は50件以内で入力してください。'
    steps = []
    for row in zip(*columns):
        item = dict(zip(keys, (value.strip() for value in row)))
        if not any(item[key] for key in ('time', 'title', 'place', 'note')):
            continue
        steps.append(item)
    for item in steps:
        if not item['day'].isdigit() or not 1 <= int(item['day']) <= 30:
            return steps, '日程は1〜30日目で指定してください。'
        if item['time'] and not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', item['time']):
            return steps, '時刻は時:分で指定してください。'
        if not item['title'] or len(item['title']) > 100 or len(item['place']) > 100 or len(item['note']) > 1000:
            return steps, '予定名は必須です。予定名・場所は100字、メモは1000字以内です。'
    return steps, None
