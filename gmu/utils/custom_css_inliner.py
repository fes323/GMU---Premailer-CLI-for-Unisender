"""
Собственное решение для инлайн-стилизации CSS с сохранением Outlook комментариев.
"""

# Отключаем предупреждения cssutils
# cssutils выводит много предупреждений о CSS-свойствах, которые не критичны для email-клиентов
import logging
import re
from typing import Dict, List, Optional, Tuple

import cssutils
from bs4 import BeautifulSoup, Comment

# Отключаем предупреждения cssutils
cssutils.log.setLevel(logging.ERROR)
# Дополнительно отключаем предупреждения через стандартный logging
logging.getLogger('cssutils').setLevel(logging.ERROR)


class CustomCSSInliner:
    """Собственный класс для инлайн-стилизации CSS с сохранением Outlook комментариев."""

    def __init__(self, html_content: str):
        self.html_content = html_content
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.css_rules = []
        self.outlook_comments = []

    def extract_css_rules(self) -> List[Dict]:
        """Извлекает CSS правила из <style> тегов и внешних файлов."""
        css_rules = []

        # Находим все <style> теги
        style_tags = self.soup.find_all('style')

        for style_tag in style_tags:
            css_text = style_tag.get_text()
            if css_text.strip():
                rules = self._parse_css_text(css_text)
                css_rules.extend(rules)

        return css_rules

    def extract_media_queries(self) -> List[str]:
        """Извлекает медиазапросы из <style> тегов."""
        media_queries = []

        # Находим все <style> теги
        style_tags = self.soup.find_all('style')

        for style_tag in style_tags:
            css_text = style_tag.get_text()
            if css_text.strip():
                # Извлекаем медиазапросы с помощью регулярных выражений
                media_pattern = r'@media[^{]+\{[^}]+\}'
                matches = re.findall(media_pattern, css_text, re.DOTALL)
                media_queries.extend(matches)

        return media_queries

    def _parse_css_text(self, css_text: str) -> List[Dict]:
        """Парсит CSS текст и возвращает список правил."""
        rules = []

        try:
            # Используем cssutils для парсинга CSS
            sheet = cssutils.parseString(css_text)

            for rule in sheet:
                if rule.type == rule.STYLE_RULE:
                    selector = rule.selectorText
                    styles = {}

                    for prop in rule.style:
                        styles[prop.name] = prop.value

                    rules.append({
                        'selector': selector,
                        'styles': styles,
                        'specificity': self._calculate_specificity(selector)
                    })

        except Exception as e:
            print(f"Ошибка парсинга CSS: {e}")

        return rules

    def _calculate_specificity(self, selector: str) -> Tuple[int, int, int, int]:
        """Вычисляет специфичность CSS селектора."""
        # Упрощенный расчет специфичности: (inline, id, class, element)
        inline = 0
        ids = len(re.findall(r'#', selector))
        classes = len(re.findall(r'\.', selector))
        elements = len(re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', selector))

        return (inline, ids, classes, elements)

    def extract_outlook_comments(self) -> List[Dict]:
        """Извлекает Outlook комментарии с их позициями."""
        outlook_comments = []

        # Паттерн для поиска Outlook комментариев
        outlook_pattern = r'<!--\[if[^>]*>.*?<!\[endif\]-->'

        for match in re.finditer(outlook_pattern, self.html_content, re.DOTALL | re.IGNORECASE):
            comment_text = match.group(0)
            start_pos = match.start()
            end_pos = match.end()

            # Проверяем, что это действительно Outlook комментарий
            if any(keyword in comment_text.lower() for keyword in ['mso', 'outlook', 'gte', 'lt']):
                outlook_comments.append({
                    'text': comment_text,
                    'start': start_pos,
                    'end': end_pos
                })

        return outlook_comments

    def apply_inline_styles(self, css_rules: List[Dict]) -> BeautifulSoup:
        """Применяет CSS правила как инлайн стили к элементам."""
        # Сортируем правила по специфичности (от меньшей к большей)
        sorted_rules = sorted(css_rules, key=lambda x: x['specificity'])

        # Собираем все стили для каждого элемента
        element_styles = {}

        for rule in sorted_rules:
            selector = rule['selector']
            styles = rule['styles']

            try:
                # Специальная обработка для псевдокласса :last-child
                if ':last-child' in selector:
                    self._collect_last_child_styles(
                        selector, styles, element_styles)
                else:
                    # Обычная обработка селекторов
                    elements = self._find_elements_by_selector(selector)
                    for element in elements:
                        element_id = id(element)
                        if element_id not in element_styles:
                            element_styles[element_id] = {
                                'element': element, 'styles': []}
                        element_styles[element_id]['styles'].append(styles)

            except Exception as e:
                print(
                    f"Ошибка применения стилей для селектора '{selector}': {e}")

        # Применяем все собранные стили к элементам
        for element_data in element_styles.values():
            element = element_data['element']
            all_styles = element_data['styles']

            # Получаем существующие инлайн стили
            existing_style = element.get('style', '')
            existing_styles = self._parse_inline_styles(existing_style)

            # Объединяем все CSS стили
            merged_css_styles = {}
            for styles in all_styles:
                merged_css_styles.update(styles)

            # Обрабатываем отдельные свойства
            processed_styles = self._process_individual_properties(
                existing_styles, merged_css_styles)

            # Объединяем стили: сначала CSS стили, потом инлайн стили (они имеют приоритет)
            merged_styles = self._merge_css_properties(
                processed_styles['existing'], processed_styles['new'])

            # Применяем стили к элементу
            if merged_styles:
                style_string = self._styles_to_string(merged_styles)
                element['style'] = style_string

        return self.soup

    def _collect_last_child_styles(self, selector: str, styles: Dict[str, str], element_styles: Dict):
        """Собирает стили для элементов с псевдоклассом :last-child."""
        # Убираем :last-child из селектора
        base_selector = selector.replace(':last-child', '').strip()

        # Находим все элементы по базовому селектору
        elements = self._find_elements_by_selector(base_selector)

        # Для каждого элемента проверяем, является ли он последним дочерним элементом
        for element in elements:
            parent = element.parent
            if parent:
                # Получаем всех дочерних элементов (не только с одинаковым именем)
                siblings = [child for child in parent.children
                            if hasattr(child, 'name') and child.name is not None]

                # Проверяем, является ли текущий элемент последним
                if siblings and element == siblings[-1]:
                    element_id = id(element)
                    if element_id not in element_styles:
                        element_styles[element_id] = {
                            'element': element, 'styles': []}
                    element_styles[element_id]['styles'].append(styles)

    def _apply_last_child_rule(self, selector: str, styles: Dict[str, str]):
        """Применяет CSS правило с псевдоклассом :last-child."""
        # Убираем :last-child из селектора
        base_selector = selector.replace(':last-child', '').strip()

        # Находим все элементы по базовому селектору
        elements = self._find_elements_by_selector(base_selector)

        # Для каждого элемента проверяем, является ли он последним дочерним элементом
        for element in elements:
            parent = element.parent
            if parent:
                # Получаем всех дочерних элементов (не только с одинаковым именем)
                siblings = [child for child in parent.children
                            if hasattr(child, 'name') and child.name is not None]

                # Проверяем, является ли текущий элемент последним
                if siblings and element == siblings[-1]:
                    self._apply_styles_to_elements([element], styles)

    def _apply_styles_to_elements(self, elements: List, styles: Dict[str, str]):
        """Применяет стили к списку элементов."""
        for element in elements:
            # Получаем существующие инлайн стили
            existing_style = element.get('style', '')
            existing_styles = self._parse_inline_styles(existing_style)

            # Обрабатываем отдельные свойства (padding-top, margin-bottom и т.д.)
            processed_styles = self._process_individual_properties(
                existing_styles, styles)

            # Объединяем стили: сначала CSS стили, потом инлайн стили (они имеют приоритет)
            merged_styles = self._merge_css_properties(
                processed_styles['existing'], processed_styles['new'])

            # Применяем стили к элементу
            if merged_styles:
                style_string = self._styles_to_string(merged_styles)
                element['style'] = style_string

    def _find_elements_by_selector(self, selector: str) -> List:
        """Находит элементы по CSS селектору."""
        elements = []

        try:
            # Обрабатываем множественные селекторы (разделенные запятыми)
            if ',' in selector:
                # Разбиваем по запятым и обрабатываем каждый селектор отдельно
                individual_selectors = [s.strip() for s in selector.split(',')]
                for individual_selector in individual_selectors:
                    elements.extend(
                        self._find_elements_by_single_selector(individual_selector))
            else:
                # Обрабатываем одиночный селектор
                elements = self._find_elements_by_single_selector(selector)

        except Exception as e:
            print(f"Ошибка поиска элементов для селектора '{selector}': {e}")

        return elements

    def _find_elements_by_single_selector(self, selector: str) -> List:
        """Находит элементы по одиночному CSS селектору."""
        elements = []

        try:
            # Используем BeautifulSoup's встроенный CSS селектор движок
            # Он поддерживает большинство CSS селекторов включая псевдоклассы
            elements = self.soup.select(selector)

        except Exception as e:
            print(f"Ошибка поиска элементов для селектора '{selector}': {e}")
            # Fallback к простому поиску для базовых селекторов
            elements = self._fallback_simple_selector(selector)

        return elements

    def _fallback_simple_selector(self, selector: str) -> List:
        """Fallback для простых селекторов, если CSS селектор не работает."""
        elements = []

        try:
            # Простая реализация для основных селекторов
            if selector.startswith('#'):
                # ID селектор
                element_id = selector[1:]
                element = self.soup.find(id=element_id)
                if element:
                    elements.append(element)

            elif selector.startswith('.'):
                # Class селектор
                class_name = selector[1:]
                elements = self.soup.find_all(class_=class_name)

            elif selector.startswith('*'):
                # Универсальный селектор
                elements = self.soup.find_all()

            else:
                # Тег селектор
                elements = self.soup.find_all(selector)

        except Exception as e:
            print(f"Ошибка fallback поиска для селектора '{selector}': {e}")

        return elements

    def _process_individual_properties(self, existing_styles: Dict[str, str], new_styles: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Обрабатывает отдельные свойства типа padding-top, margin-bottom и объединяет их с основными."""
        processed_existing = existing_styles.copy()
        processed_new = new_styles.copy()

        # Обрабатываем padding
        padding_individual = {}
        for prop in ['padding-top', 'padding-right', 'padding-bottom', 'padding-left']:
            if prop in processed_existing:
                padding_individual[prop] = processed_existing.pop(prop)

        if padding_individual:
            # Объединяем отдельные padding свойства в одно
            combined_padding = self._combine_individual_box_properties(
                'padding', padding_individual)
            if 'padding' in processed_existing:
                # Объединяем с существующим padding
                processed_existing['padding'] = self._combine_box_property(
                    'padding', processed_existing['padding'], combined_padding)
            else:
                processed_existing['padding'] = combined_padding

        # Обрабатываем margin
        margin_individual = {}
        for prop in ['margin-top', 'margin-right', 'margin-bottom', 'margin-left']:
            if prop in processed_existing:
                margin_individual[prop] = processed_existing.pop(prop)

        if margin_individual:
            # Объединяем отдельные margin свойства в одно
            combined_margin = self._combine_individual_box_properties(
                'margin', margin_individual)
            if 'margin' in processed_existing:
                # Объединяем с существующим margin
                processed_existing['margin'] = self._combine_box_property(
                    'margin', processed_existing['margin'], combined_margin)
            else:
                processed_existing['margin'] = combined_margin

        return {
            'existing': processed_existing,
            'new': processed_new
        }

    def _combine_individual_box_properties(self, property_name: str, individual_properties: Dict[str, str]) -> str:
        """Объединяет отдельные свойства типа padding-top в сокращенную форму."""
        # Создаем массив значений [top, right, bottom, left]
        values = ['0', '0', '0', '0']

        if property_name == 'padding':
            if 'padding-top' in individual_properties:
                values[0] = individual_properties['padding-top']
            if 'padding-right' in individual_properties:
                values[1] = individual_properties['padding-right']
            if 'padding-bottom' in individual_properties:
                values[2] = individual_properties['padding-bottom']
            if 'padding-left' in individual_properties:
                values[3] = individual_properties['padding-left']
        elif property_name == 'margin':
            if 'margin-top' in individual_properties:
                values[0] = individual_properties['margin-top']
            if 'margin-right' in individual_properties:
                values[1] = individual_properties['margin-right']
            if 'margin-bottom' in individual_properties:
                values[2] = individual_properties['margin-bottom']
            if 'margin-left' in individual_properties:
                values[3] = individual_properties['margin-left']

        # Возвращаем в сокращенной форме
        if len(set(values)) == 1:
            # Все значения одинаковые
            return values[0]
        elif values[0] == values[2] and values[1] == values[3]:
            # Вертикальные и горизонтальные значения одинаковые
            return f"{values[0]} {values[1]}"
        else:
            # Все значения разные
            return ' '.join(values)

    def _parse_inline_styles(self, style_string: str) -> Dict[str, str]:
        """Парсит строку инлайн стилей в словарь."""
        styles = {}

        if style_string:
            # Разбиваем по точкам с запятой
            declarations = style_string.split(';')

            for declaration in declarations:
                if ':' in declaration:
                    prop, value = declaration.split(':', 1)
                    styles[prop.strip()] = value.strip()

        return styles

    def _merge_css_properties(self, existing_styles: Dict[str, str], new_styles: Dict[str, str]) -> Dict[str, str]:
        """Умно объединяет CSS свойства, учитывая сокращенные формы."""
        merged = existing_styles.copy()

        for prop, value in new_styles.items():
            if prop in merged:
                # Объединяем свойства
                merged[prop] = self._combine_css_property(
                    prop, merged[prop], value)
            else:
                merged[prop] = value

        return merged

    def _combine_css_property(self, property_name: str, existing_value: str, new_value: str) -> str:
        """Объединяет значения CSS свойства."""
        # Специальная обработка для padding и margin
        if property_name in ['padding', 'margin']:
            return self._combine_box_property(property_name, existing_value, new_value)

        # Для остальных свойств инлайн стили имеют приоритет
        return existing_value

    def _combine_box_property(self, property_name: str, existing_value: str, new_value: str) -> str:
        """Объединяет значения для padding и margin."""
        # Парсим существующее значение
        existing_values = self._parse_box_values(existing_value)

        # Парсим новое значение
        new_values = self._parse_box_values(new_value)

        # Объединяем значения
        combined_values = []
        for i in range(4):  # top, right, bottom, left
            if i < len(existing_values) and existing_values[i] is not None:
                combined_values.append(existing_values[i])
            elif i < len(new_values) and new_values[i] is not None:
                combined_values.append(new_values[i])
            else:
                combined_values.append('0')

        # Возвращаем объединенное значение
        if len(set(combined_values)) == 1:
            # Все значения одинаковые
            return combined_values[0]
        elif combined_values[0] == combined_values[2] and combined_values[1] == combined_values[3]:
            # Вертикальные и горизонтальные значения одинаковые
            return f"{combined_values[0]} {combined_values[1]}"
        else:
            # Все значения разные
            return ' '.join(combined_values)

    def _parse_box_values(self, value: str) -> List[str]:
        """Парсит значения для padding/margin в список [top, right, bottom, left]."""
        if not value or value.strip() == '':
            return ['0', '0', '0', '0']

        values = value.strip().split()

        if len(values) == 1:
            # Одно значение: применяется ко всем сторонам
            return [values[0], values[0], values[0], values[0]]
        elif len(values) == 2:
            # Два значения: вертикальные и горизонтальные
            return [values[0], values[1], values[0], values[1]]
        elif len(values) == 3:
            # Три значения: верх, горизонтальные, низ
            return [values[0], values[1], values[2], values[1]]
        elif len(values) == 4:
            # Четыре значения: верх, право, низ, лево
            return values
        else:
            # Неизвестный формат, возвращаем как есть
            return [value] + ['0'] * 3

    def _styles_to_string(self, styles: Dict[str, str]) -> str:
        """Преобразует словарь стилей в строку."""
        return '; '.join([f"{prop}: {value}" for prop, value in styles.items()])

    def remove_style_tags(self) -> BeautifulSoup:
        """Удаляет <style> теги после применения инлайн стилей, но сохраняет медиазапросы."""
        # Удаляем только обычные style теги, не те что внутри Outlook комментариев
        style_tags = self.soup.find_all('style')
        for tag in style_tags:
            # Проверяем, не находится ли тег внутри Outlook комментария
            if not self._is_inside_outlook_comment(tag):
                # Проверяем, содержит ли тег медиазапросы
                css_text = tag.get_text()
                if self._contains_media_queries(css_text):
                    # Если содержит медиазапросы, оставляем только их
                    media_queries = self._extract_media_queries_from_text(
                        css_text)
                    if media_queries:
                        tag.string = '\n'.join(media_queries)
                    else:
                        tag.decompose()
                else:
                    # Если не содержит медиазапросы, удаляем полностью
                    tag.decompose()

        return self.soup

    def _contains_media_queries(self, css_text: str) -> bool:
        """Проверяет, содержит ли CSS текст медиазапросы."""
        return '@media' in css_text

    def _extract_media_queries_from_text(self, css_text: str) -> List[str]:
        """Извлекает медиазапросы из CSS текста."""
        media_queries = []

        # Находим все позиции @media
        media_positions = []
        for match in re.finditer(r'@media', css_text):
            media_positions.append(match.start())

        for pos in media_positions:
            # Находим начало медиазапроса
            start = pos
            # Находим открывающую фигурную скобку
            brace_start = css_text.find('{', start)
            if brace_start == -1:
                continue

            # Подсчитываем фигурные скобки для правильного закрытия
            brace_count = 0
            end = brace_start

            for i in range(brace_start, len(css_text)):
                if css_text[i] == '{':
                    brace_count += 1
                elif css_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break

            if brace_count == 0:
                media_query = css_text[start:end]
                media_queries.append(media_query)

        return media_queries

    def _is_inside_outlook_comment(self, element) -> bool:
        """Проверяет, находится ли элемент внутри Outlook комментария."""
        # Получаем родительский элемент
        parent = element.parent

        while parent:
            # Проверяем, является ли родитель комментарием
            if isinstance(parent, Comment):
                comment_text = str(parent)
                if any(keyword in comment_text.lower() for keyword in ['mso', 'outlook', 'gte', 'lt']):
                    return True

            parent = parent.parent

        return False

    def process(self) -> str:
        """Основной метод обработки HTML с инлайн-стилизацией."""
        # 1. Извлекаем CSS правила
        css_rules = self.extract_css_rules()

        # 2. Извлекаем Outlook комментарии
        outlook_comments = self.extract_outlook_comments()

        # 3. Применяем инлайн стили
        self.apply_inline_styles(css_rules)

        # 4. Удаляем <style> теги
        self.remove_style_tags()

        # 5. Возвращаем обработанный HTML
        return str(self.soup)


def inline_css_custom(html_content: str) -> str:
    """Функция для инлайн-стилизации CSS с сохранением Outlook комментариев."""
    inliner = CustomCSSInliner(html_content)
    return inliner.process()
