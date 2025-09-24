<<<<<<< HEAD
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Arryn_Back.infrastructure.config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
=======
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Arryn_Back.infrastructure.config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
>>>>>>> origin/feature/SCRUM-125-Implementar-identificador-de-ofertas-por-categoría
