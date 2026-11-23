import unittest
from datetime import datetime
from django.test.runner import DiscoverRunner
from docx import Document


class DocxTestResult(unittest.TextTestResult):
    """Сборщик результатов каждого теста для экспорта в Word."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_records = []

    def _get_description(self, test):
        doc = test.shortDescription()
        return doc if doc else "Без описания"

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_records.append({
            'name': str(test),
            'description': self._get_description(test),
            'status': 'УСПЕШНО (PASSED)',
            'details': '—'
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_records.append({
            'name': str(test),
            'description': self._get_description(test),
            'status': 'ПРОВАЛЕНО (FAILED)',
            'details': self._exc_info_to_string(err, test)
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.test_records.append({
            'name': str(test),
            'description': self._get_description(test),
            'status': 'ОШИБКА (ERROR)',
            'details': self._exc_info_to_string(err, test)
        })


class WordExportTestRunner(DiscoverRunner):
    """Кастомный Django Test Runner, сохраняющий итоги тестирования в test_results.docx."""

    def get_resultclass(self):
        return DocxTestResult

    def run_suite(self, suite, **kwargs):
        result = super().run_suite(suite, **kwargs)
        self.export_to_word(result)
        return result

    def export_to_word(self, result):
        doc = Document()
        doc.add_heading('Отчёт о тестировании проекта Horse Tours', level=1)
        doc.add_paragraph(f'Дата и время запуска: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')

        total = result.testsRun
        failed = len(result.failures)
        errors = len(result.errors)
        passed = total - failed - errors

        doc.add_heading('Сводка результатов', level=2)
        summary_table = doc.add_table(rows=1, cols=4)
        summary_table.style = 'Table Grid'
        hdr = summary_table.rows[0].cells
        hdr[0].text = 'Всего тестов'
        hdr[1].text = 'Успешно'
        hdr[2].text = 'Провалено'
        hdr[3].text = 'Ошибок'

        row = summary_table.add_row().cells
        row[0].text = str(total)
        row[1].text = str(passed)
        row[2].text = str(failed)
        row[3].text = str(errors)

        doc.add_heading('Детальные результаты тестов', level=2)
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        headers = table.rows[0].cells
        headers[0].text = 'Тест-метод'
        headers[1].text = 'Описание проверки'
        headers[2].text = 'Статус'
        headers[3].text = 'Примечания'

        for record in getattr(result, 'test_records', []):
            r = table.add_row().cells
            r[0].text = record['name']
            r[1].text = record['description']
            r[2].text = record['status']
            r[3].text = record['details']

        filename = 'test_results.docx'
        doc.save(filename)
        print(f"\n[WORD EXPORT] Результаты тестов успешно сохранены в файл: {filename}")