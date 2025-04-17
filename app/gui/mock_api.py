def mock_send_messages_request(date: str):
    return {"messages_received": 10, "reports_saved": 7}

def mock_get_reports(date: str):
    return [
        {
            "Дата": date,
            "Подразделение": "ЮГ",
            "Операция": "Пахота",
            "Культура": "Пшеница озимая",
            "За день, га": 32,
            "С начала операции, га": 352,
            "Вал за день, ц": None,
            "Вал с начала, ц": None
        },
        # ...
    ]

def mock_save_excel(date: str, path: str):
    return f"{path}/report_{date}.xlsx"
