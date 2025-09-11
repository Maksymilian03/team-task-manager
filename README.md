# Team Task Manager – System Zarządzania Zadaniami

Projekt stworzony w ramach pracy licencjackiej. Celem aplikacji jest umożliwienie efektywnego zarządzania zadaniami i zespołami projektowymi.

## Opis

Team Task Manager to aplikacja webowa oparta na Django REST Framework, umożliwiająca:
- tworzenie i przydzielanie zadań,
- przypisywanie użytkowników do zespołów,
- filtrowanie po statusie, priorytecie i kategorii,
- komentowanie zadań oraz podgląd historii zmian (log audytu),
- zarządzanie kategoriami zadań,
- uwierzytelnianie i autoryzację użytkowników z użyciem JWT.

## Technologie

- Python 3.13
- Django
- Django REST Framework
- PostgreSQL
- Postman (testowanie API)
- Git, GitHub

## Funkcjonalności

- [x] Rejestracja i logowanie użytkowników (JWT)
- [x] Tworzenie zespołów (`teams`)
- [x] Tworzenie zadań (`tasks`) z priorytetem, statusem, terminem i kategorią
- [x] Przypisywanie zadań do użytkowników (`assigned_to`)
- [x] Komentarze do zadań (`comments`)
- [x] Historia zmian (`logs`)
- [x] Filtrowanie i sortowanie
- [x] Uprawnienia na poziomie zadań
- [x] Dashboard z podsumowaniem zadań wg statusów
- [ ] 🔜 Integracja z kalendarzami chmurowymi (Google / Outlook)

## Jak uruchomić projekt lokalnie

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/Maksymilian03/team-task-manager
   cd team-task-manager
   ```

2. Stwórz wirtualne środowisko i aktywuj:
   ```bash
   python -m venv venv
   source venv/bin/activate  # lub venv\Scripts\activate na Windows
   ```

3. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```

4. Wykonaj migracje i uruchom serwer:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. (Opcjonalnie) Stwórz superużytkownika:
   ```bash
   python manage.py createsuperuser
   ```

## Uwierzytelnianie

API używa JWT. Aby uzyskać token:
```http
POST /api/token/
```
Przykład użycia w nagłówkach:
```http
Authorization: Bearer <twój_token>
```

## Struktura API

- `/api/teams/`
- `/api/tasks/`
- `/api/categories/`
- `/api/comments/`
- `/api/logs/`
- `/api/token/`
- `/api/register/`

## Licencja

Projekt dostępny na licencji MIT – możesz używać, kopiować i modyfikować z podaniem autora.

---

## Autor

Maksymilian Stolarek
Projekt wykonany w ramach pracy licencjackiej na [WSB Merito Wrocław]  
Rok: 2025
