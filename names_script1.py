from collections import Counter
import os
import re
from bs4 import BeautifulSoup
import pandas as pd

NAMES_PATTERN = re.compile(r'((\bупомянутые\b)|((\bименной\b)?\bуказатель\b))'
                           r'(\s{,2})?((\bим[её]н.?\b:?\s+?)|(\bлица\b:?\s+?))?', re.I)
AUTHOR_PATTERN = re.compile(r'\s+?[А-Я]\. [А-Я][а-яё]{,20}(\s+)?$')


def get_names(path):
    """
    принимает путь к файлу и возвращает из него имена с метаинфой, если они есть
    """
    with open(path, 'r', encoding='utf-8') as file:
        html = file.read()
    soup = BeautifulSoup(html, features='html.parser')
    for tag in soup.find_all('p'):
        text = tag.text
        if 'упомянутые' in text.lower() or 'указатель' in text.lower():
            names = text.split(NAMES_PATTERN.search(text).group(0), 1)[1]
            names = AUTHOR_PATTERN.sub('', names)
            return names
    return None


def get_filenames_fios_metainfos(directory):
    """
    принимает путь к директории и возвращает из нее названия файлов, имена и метаинфу по отдельности
    """
    filenames = []
    fios = []
    metainfos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                if get_names(file):
                    print(file)
                    names = get_names(file)
                    semicolon_amount = Counter(names)[';']
                    n_amount = Counter(names)['\n']
                    if semicolon_amount > n_amount:
                        first_separator = ';'
                    else:
                        first_separator = '\n'
                    splitted_names = names.split(first_separator)
                    sep_pattern = re.compile(r'(–|,|—|:|( (?={))|( - )|'
                                             r'( \b(?=[а-я])))(?![^\(\[]*[\)\]])')
                    for index, name in enumerate(splitted_names):
                        if sep_pattern.search(name):
                            splitted_names[index] = sep_pattern.sub('@', name, 1)
                    for index, name in enumerate(splitted_names):
                        if type(name) == str:
                            splitted_names[index] = name.split('@', 1)
                    for index, name in enumerate(splitted_names):
                        if type(name) == list:
                            splitted_names[index] = [item.strip() for item in name]
                        else:
                            splitted_names[index] = name.strip()
                    for name in splitted_names:
                        if type(name) == list:
                            if name[0]:
                                filenames.append(file)
                                fios.append(name[0])
                                if len(name) > 1:
                                    metainfos.append(name[1])
                                else:
                                    metainfos.append(None)
                        else:
                            if name:
                                fios.append(name)
                                metainfos.append(None)
                                filenames.append(file)
    return filenames, fios, metainfos


def get_supertable(filenames, fios, metainfos):
    """
    принимает названия файлов, имена и метаинфу
    и возвращает таблицу из трех столбцов с названиями файлов, именами людей и метаинфой
    """
    supertable = pd.DataFrame(
            {'Название файла': filenames,
             'ФИО': fios,
             'Метаинформация': metainfos
             })
    return supertable


def get_index_list(seq, item):
    """
    принимает последовательность и элемент
    и возвращает список индексов этого элемента в этой последовательности
    """
    start_at = -1
    locs = []
    while True:
        try:
            loc = seq.index(item, start_at+1)
        except ValueError:
            break
        else:
            locs.append(loc)
            start_at = loc
    return locs


def get_table_with_ids(supertable):
    """
    принимает датафрейм, сопоставляет его с бд
    и возвращает его с новым столбцом совпаших айди
    """
    fios = [re.sub(r'[\(\[].+?[\]\)]', '', fio) for fio in list(supertable['ФИО'])]
    database = pd.read_csv('persons.csv')
    database_fios = list(database.ViewInfoName)
    ids = [get_index_list(database_fios, fio) if fio in database_fios else None for fio in fios]
    supertable['Совпавшие id'] = [', '.join(map(str, item)) if type(item) == list else item for item in ids]
    return supertable


def main():
    filenames, fios, metainfos = get_filenames_fios_metainfos('.')
    supertable = get_table_with_ids(get_supertable(filenames, fios, metainfos))
    supertable.to_excel('supertable_supernew.xlsx', index=False)


if __name__ == '__main__':
    main()

расстояние левенштейна
