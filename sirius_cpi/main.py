from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import numpy as np
import os
from pprint import pprint
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

department_question_weights = {
    "Контрактные услуги": {
        "Соответствует ли результат проведения работ/услуг по договору вашим ожиданиям?": 20,
        "Соответствует ли срок проведения работ/услуг по договору вашим ожиданиям?": 15,
        "Соответствует ли стоимость работ/услуг по договору вашим ожиданиям?": 15,
        "Как вы оцениваете качество административной поддержки по договору?": 15,
        "Соответствует ли срок согласования договора ожидаемому?": 15,
        "Соответствует ли уровень компетенций специалистов-исследователей ожидаемому?": 20,
    },
    "ДПО": {
        "Соответствует ли программа образовательного модуля вашим ожиданиям?": 25,
        "Соответствует ли уровень компетенций преподавателей программы ожидаемому?": 25,
        "Оцените программу курса по критериям     [Полезность информации]": 5,
        "Оцените программу курса по критериям     [Сложность программы]": 5,
        "Оцените программу курса по критериям     [Доступность изложения материала]": 5,
        "Оцените программу курса по критериям     [Соотношение теории и практики]": 5,
        "Оцените программу курса по критериям     [Полезность практических занятий]": 5,
        "Оцените программу курса по критериям     [Полнота и доступность ответов на вопросы аудитории]": 5,
        "Оцените организационное сопровождение программы     [Информационное сопровождение до начала и в течение программы организаторами]": 5,
        "Оцените организационное сопровождение программы     [Материально-техническое обеспечение]": 5,
        "Оцените организационное сопровождение программы     [Проживание]": 5,
        "Оцените организационное сопровождение программы     [Питание]": 5,
    },
    "ЕН": {
        "Как вы оцениваете время выполнения запросов?": 30,
        "Как вы оцениваете оснащенность предоставленной зоны?": 20,
        "Как вы оцениваете качество взаимодействия (телефон, e-mail, лично) и консультаций по работе?": 30,
        "Какая в целом ваша оценка работы подразделения?": 20,
    },
    "ИТО": {
        'Как вы оцениваете проведение пуско-наладочных работ?     [Качество]': 7.5,
        'Как вы оцениваете проведение пуско-наладочных работ?     [Сроки]': 7.5,
        'Как вы оцениваете проведение планового технического обслуживания оборудования?     [Качество]': 7.5,
        'Как вы оцениваете проведение планового технического обслуживания оборудования?     [Сроки]': 7.5,
        'Как вы оцениваете проведение ремонта оборудования?     [Качество]': 7.5,
        'Как вы оцениваете проведение ремонта оборудования?     [Сроки]': 7.5,
        'Как вы оцениваете метрологическое обеспечение оборудования (поверка, аттестация)?     [Качество]': 7.5,
        'Как вы оцениваете метрологическое обеспечение оборудования (поверка, аттестация)?     [Сроки]': 7.5,
        'Как вы оцениваете снабжение медицинскими газами и криожидкостями?  [Качество]': 5,
        'Как вы оцениваете снабжение медицинскими газами и криожидкостями?  [Сроки]': 5,
        'Как вы оцениваете информационную систему подачи заявок ServiceDesk "Сервис лабораторного оборудования" для обращений в инженерно-технический отдел?': 10,
        'Какая в целом ваша оценка работы подразделения?': 20,
    },
    "Ресурсные центры": {
        "Как вы оцениваете качество/достоверность предоставляемых результатов?": 25,
        "Как вы оцениваете время выполнения сервисных услуг?": 25,
        "Как вы оцениваете консультации по профильным (профессиональным) вопросам?": 10,
        "Как вы оцениваете качество взаимодействия (телефон, e-mail, лично)?": 10,
        "Как вы оцениваете понятность/полезность выдаваемой интерпретации или отчетов?": 10,
        "Как вы оцениваете объем оказываемых услуг (оснащенность)?": 5,
        "Какая в целом ваша оценка работы подразделения?": 15,
    },
        "ОЛП": {
        # 'Как вы оцениваете работу группы лаборантов-координаторов?': 25,
        'Как вы оцениваете работу группы по лабораторному обеспечению?': 25,
        'Как вы оцениваете сервис обработки и технического заведения вашей заявки на обеспечение в 1С:УХ?     [Простота и удобство при подаче заявки на обеспечение]': 10,
        'Как вы оцениваете сервис обработки и технического заведения вашей заявки на обеспечение в 1С:УХ?     [Корректность при уточнении параметров заявки специалистом]': 10,
        'Как вы оцениваете сервис обработки и технического заведения вашей заявки на обеспечение в 1С:УХ?     [Скорость заведения заявок в 1С:УХ специалистами лабораторного обеспечения]': 12,
        'Как вы оцениваете доставку ТМЦ со складов НТУ и ЛК?     [Простота и удобство использования сервиса]': 10,
        'Как вы оцениваете доставку ТМЦ со складов НТУ и ЛК?     [Скорость доставки]': 5,
        'Как вы оцениваете доставку ТМЦ со складов НТУ и ЛК?     [Информирование о поступлении ТМЦ на склад]': 10,
        'Как вы оцениваете удобство работы с реестрами?     [Реестр реактивов и материалов]': 6,
        'Как вы оцениваете удобство работы с реестрами?     [Реестр оборудования]': 6,
        'Как вы оцениваете удобство работы с реестрами?     [Реестр склада ЛВЖ]': 6,
        'Как вы оцениваете работу группы общелабораторного сервиса?': 12,
        'Как вы оцениваете лабораторную уборку, которую проводят лаборанты ЛК?     [Качество ежедневной лабораторной уборки]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят лаборанты ЛК?     [Периодичность лабораторной уборки]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят лаборанты ЛК?     [Качество генеральной лабораторной уборки помещений]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят лаборанты ЛК?     [Качество генеральной лабораторной уборки оборудования]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят лаборанты ЛК?     [Срок и качество реализации  лабораторной уборки по требованию]': 10,
        'Как вы оцениваете сервис стерилизации и мытья посуды?     [Сроки и качество стерилизации]': 5,
        'Как вы оцениваете сервис стерилизации и мытья посуды?     [Сроки и качество мытья посуды]': 5,
        'Как вы оцениваете сервис обеспечения СИЗ (средства индивидуальной защиты)?     [Выдача. Удобство сервиса и время выдачи]': 7,
        'Как вы оцениваете сервис обеспечения СИЗ (средства индивидуальной защиты)?     [Характеристики. Качество выдаваемых СИЗ, номенклатурный и размерный ряды]': 7,
        'Как вы оцениваете сервис обеспечения СИЗ (средства индивидуальной защиты)?     [Стирка. Качество и скорость стирки]': 7,
        'Как вы оцениваете сервис обеспечения СИЗ (средства индивидуальной защиты)?     [Стирка. Удобство сдачи и получения СИЗ]': 7,
        'Как вы оцениваете работу группы содержания лабораторных помещений (группы клининга)?': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят уборщики общественных территорий?     [Качество рутинной (ежедневной) уборки]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят уборщики общественных территорий?     [Периодичность уборки]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят уборщики общественных территорий?     [Качество генеральной уборки]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят уборщики общественных территорий?     [Срок реализации уборки по требованию]': 10,
        'Как вы оцениваете лабораторную уборку, которую проводят уборщики общественных территорий?     [Взаимодействие с уборщиками]': 10,
        'Как вы оцениваете работу администратора ЛК?     [Скорость ответа на запрос в чате "Большой ЛК" либо при обращении по телефону]': 10,
        'Как вы оцениваете работу администратора ЛК?     [Информирование о статусе поданной заявки]': 5,
        'Как вы оцениваете работу администратора ЛК?     [Контроль санитарно-эпидемиологического режима "заразной" зоны]': 5,
        'Как вы оцениваете работу администратора ЛК?     [Обеспечение обеззараживания помещений ЛК УФ-облучением]': 5,
        'Как вы оцениваете работу администратора ЛК?     [Взаимодействие с администраторами]': 15,
    },

}


department_question_no_weights_second = {
    "ИТО": [
        "Оцените работу Белоусова Евгения Васильевича",
        "Оцените работу Довгалева Глеба Витальевича",
        "Оцените работу Комарова Андрея Александровича", 
        "Оцените работу Кудякова Владимира Юрьевича",
        "Оцените работу Пархачева Александра Алексеевича", 
        "Оцените работу Савельева Дениса Сергеевича",  
        "Оцените работу Толкачевой Ларисы Викторовны", 
    ],
    "ОЛП": [
        "Как вы оцениваете работу руководителя отдела лабораторной поддержки Шумовой Валентины Сергеевны?", 
        "Как вы оцениваете работу Акуловой Анастасии Эдуардовны?", 
        "Как вы оцениваете работу Алямской Анны Андреевны?",
        "Как вы оцениваете работу Андреевой Юлии Сергеевны?", 
        "Как вы оцениваете работу Гусмановой Ирины Сергеевны?", 
        "Как вы оцениваете работу Краснобородкиной Марии Александровны?",
        "Как вы оцениваете работу Старостиной Ирины Александровны?", 
        "Как вы оцениваете работу Гноевой Жанны Евгеньевны?",
        "Как вы оцениваете работу Высоцкой Ларисы Ивановны?",
        "Как вы оцениваете работу Нияскуловой Галины Анатольевны?", 
        "Как вы оцениваете работу Усовой Елены Юрьевны?", 
        "Как вы оцениваете работу Кабаковой Айгуль Александровны?",  
        "Как вы оцениваете работу Кревской Анны Юрьевны?",     
    ],
    "ЕН": [
        "Оцените работу Манаховой Карины Айратовны",
        "Оцените работу Осиповой Марии Александровны",
        "Оцените работу Скосаревой Евгении Сергеевны", 
        "Оцените работу Фрейдин Григория Семеновича",
    ],
    "РЦ_АМ": [
        "Оцените работу Анисимова Станислава Сергеевича",
        "Оцените работу Артамонова Ивана Владимировича", 
        "Оцените работу Афонина Михаила Борисовича", 
        "Оцените работу Винальева Андрея Александровича", 
        "Оцените работу Головина Евгения Валерьевича",
        "Оцените работу Голубковой Елены Александровны",
        "Оцените работу Кривич Татьяны Евгеньевны",
        "Оцените работу Месонжник Натальи Владимировны",
        "Оцените работу Новиковой Екатерины Сергеевны",
        "Оцените работу Рычковой Екатерины Владиславовны",   
    ],
    "РЦ_БМ": [
        "Оцените работу Милаш Наталии Валериевны",
        "Оцените работу Субчевой Елены Николаевны", 
    ],
    "РЦ_БП": [
        "Оцените работу Бойко Алены Игоревны",
        "Оцените работу Вишняковой Натальи Алексеевны", 
        "Оцените работу Волошина Данила Юрьевича", 
        "Оцените работу Краснова Ильи Александровича", 
        "Оцените работу Прокофьевой Ольги Васильевны", 
        "Оцените работу Черентаевой Анны Владимировны",
        "Оцените работу Шестаковой Ольги Васильевны",
        "Оцените работу Якшиной Юлии Игоревны",   
    ],
    "РЦ_ГИ": [
        "Оцените работу Альметовой Гузель Гависовны",
        "Оцените работу Дамбаевой Билигмы Александровны", 
        "Оцените работу Долговой Елены Анатольевны",
        "Оцените работу Колосовой Елены Сергеевны",
        "Оцените работу Хлебниковой Эллины Николаевны",
        "Оцените работу Черкасовой Екатерины Евгеньевны",
        "Оцените работу Якшина Дмитрия Михайловича",
    ],
    "РЦ_ГЦ": [
        "Оцените работу Жоховой Лады Владимировны",
        "Оцените работу Манахова Андрея Дмитриевича",
        "Оцените работу Ромашовой Марины Анатольевны", 
    ],
    "РЦ_ДКИ": [
        "Оцените работу Крапивина Богдана Николаевича",
        "Оцените работу Ситиковой Веры Анатольевны", 
    ],
    "РЦ_КОГНИ": [
        "Оцените работу Матюша Валерии Сергеевны",
        "Оцените работу Мачневой Владилены Сергеевны", 
    ],
    "РЦ_КТ": [
        "Оцените работу Кувшиновой Юлии Александровны",
        "Оцените работу Лактюшкина Виктора Сергеевича", 
        "Оцените работу Рыбцова Станислава Александровича",
        "Оцените работу Сухих Артема Александровича", 
        "Оцените работу Терещенко Валерия Павловича", 
        "Оцените работу Шумеева Александра Николаевича",  
    ],
    "РЦ_МИС": [
        "Оцените работу Афаневича Ивана Андреевича",
        "Оцените работу Баскова Егора Петровича",
        "Оцените работу Гусева Дениса Григорьевича", 
        "Оцените работу Махаткова Александра Викторовича",
        "Оцените работу Огаркова Владислава Сергеевича",
        "Оцените работу Окуневой Анны Сергеевны",     
    ],
    "РЦ_МХ": [
        "Оцените работу Андоралова Александра Михайловича",
        "Оцените работу Гутенева Алексея Александровича",
        "Оцените работу Джавадова Руслана Рауф Оглы",
        "Оцените работу Лисовской Полины Витальевны",
        "Оцените работу Литвиновой Нины Вадимовны",
        "Оцените работу Пашковой Эрики Владимировны",
        "Оцените работу Пушкина Сергея Владимировича",
        "Оцените работу Роздяловской Светланы Валентиновны", 
        "Оцените работу Черепановой Надежды Дмитриевны", 
        "Оцените работу Юнина Максима Александровича",      
    ],
    "РЦ_Р": [
        "Оцените работу Алексеенко Александра Геннадьевича",
        "Оцените работу Балясникова Григория Алексеевича",
        "Оцените работу Вартанова Олега Станиславовича",
        "Оцените работу Фарафонтова Максима Андреевича",
        "Оцените работу Шевердяева Александра Борисовича",
    ],
}


score_mapping = {
    "Не соответствует ожиданиям": 0,
    "Значительно ниже ожиданий": 50,
    "Ниже ожиданий": 75,
    "Частично ниже ожиданий": 90,
    "Соответствует ожиданиям": 100,
    "Выше ожиданий": 125,
    "Превосходит все ожидания": 150,
    "Не взаимодействовал(-а)": np.nan
}


@app.get("/", response_class=HTMLResponse)
async def department_selection(request: Request):
    departments = list(department_question_weights.keys())
    return templates.TemplateResponse("department_selection.html", {"request": request, "departments": departments})

@app.get("/department/{department_name}/", response_class=HTMLResponse)
async def department_page(request: Request, department_name: str):
    return templates.TemplateResponse("upload.html", {"request": request, "department": department_name})


@app.get("/uploadSecond", response_class=HTMLResponse)
async def upload_second_page(request: Request):
    # Список отделов для отображения
    departments = list(department_question_no_weights_second.keys())
    return templates.TemplateResponse("upload_second.html", {
        "request": request, 
        "departments": departments
    })




@app.post("/process-file/")
async def process_file(file: UploadFile = File(...), department: str = Form(...)):
    try:
        input_df = pd.read_excel(file.file)
    except Exception as e:
        return {"error": "Invalid file format or content", "details": str(e)}

    input_df.columns = input_df.columns.str.strip()

    if department not in department_question_weights:
        return {"error": f"Unknown department: {department}"}

    question_weights = department_question_weights[department]
    question_columns = [col for col in input_df.columns if col in question_weights]

    questions_to_copy = input_df.columns.tolist()
    print("Questions in the uploaded file:")
    for question in questions_to_copy:
        print(question)

    if not question_columns:
        return {
            "error": "No valid question columns found in input data",
            "available_columns": input_df.columns.tolist()
        }

    processed_rows = []
    for col in question_columns:
        temp_df = input_df[[col]].copy()
        temp_df.rename(columns={col: "оценка"}, inplace=True)
        temp_df["Вопрос"] = col
        temp_df["Вес"] = question_weights.get(col, 0)
        temp_df["оценка"] = temp_df["оценка"].replace(score_mapping)
        temp_df = temp_df[temp_df["оценка"].notna()]
        processed_rows.append(temp_df)
    print(processed_rows)

    if not processed_rows:
        return {"error": "No valid data to process"}

    processed_df = pd.concat(processed_rows, ignore_index=True)
    average_df = processed_df.groupby("Вопрос", as_index=False).agg({
        "оценка": "mean",
        "Вес": "first"
    })
    average_df['оценка с учетом веса, %'] = (
        average_df['оценка'] * average_df['Вес'] / 100
    ).round(1)

    overall_score = average_df['оценка с учетом веса, %'].sum().round(1)
    summary_row = {
        "Вопрос": f"Итоговая оценка для отдела: {department}" if department else "Итоговая оценка",
        "оценка с учетом веса, %": overall_score,
        "оценка": np.nan,
        "Вес": np.nan
    }
    average_df = pd.concat([average_df, pd.DataFrame([summary_row])], ignore_index=True)
    output_file = f"{department}_processed_data.xlsx" if department else "processed_data.xlsx"
    average_df.to_excel(output_file, index=False)


    return FileResponse(output_file, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=output_file)


@app.post("/calculate-department-score-second/")
async def calculate_department_score_second(file: UploadFile = File(...), department: str = Form(...)):
    try:
        input_df = pd.read_excel(file.file)
    except Exception as e:
        return {"error": "Invalid file format or content", "details": str(e)}

    input_df.columns = input_df.columns.str.strip()
    # Проверка на существование отдела в новом словаре
    if department not in department_question_no_weights_second:
        return {"error": f"Unknown department: {department}"}

    questions = department_question_no_weights_second[department]


    question_columns = [col for col in input_df.columns if col in questions]

    if not question_columns:
        return {
            "error": "No valid question columns found in input data",
            "available_columns": input_df.columns.tolist()
        }

    processed_rows = []
    for col in question_columns:
        temp_df = input_df[[col]].copy()
        temp_df.rename(columns={col: "оценка"}, inplace=True)
        temp_df["Вопрос"] = col
        temp_df["оценка"] = temp_df["оценка"].replace(score_mapping)
        temp_df = temp_df[temp_df["оценка"].notna()]
        
        processed_rows.append(temp_df)
    if not processed_rows:
        return {"error": "No valid data to process"}

    processed_df = pd.concat(processed_rows, ignore_index=True)

    # Вычисляем среднее значение по каждому вопросу для отдела
    average_df = processed_df.groupby("Вопрос", as_index=False).agg({
        "оценка": "mean",
    })

    # Добавляем процентное значение
    average_df['оценка, %'] = average_df['оценка'].round(1)

    # Возвращаем файл с результатами
    output_file = f"{department}_average_scores_second.xlsx" if department else "average_scores_second.xlsx"
    average_df.to_excel(output_file, index=False)

    return FileResponse(output_file, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=output_file)
