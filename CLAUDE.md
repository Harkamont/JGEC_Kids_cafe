# JGEC KIDS Reservation System Guide

## Development Commands
- Run server: `python app.py`
- Docker build: `docker build -t jgec-kids-res-sys .`
- Docker run: `docker run -p 5000:5000 jgec-kids-res-sys`
- Install requirements: `pip install -r requirements.txt`

## Code Style Guidelines
- **Formatting**: Use 4-space indentation, 88 character line limit
- **Imports**: Group imports (standard library, third-party, local) with blank lines between groups
- **Naming**: Use snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Use try/except blocks with specific exceptions
- **Templates**: HTML templates use double quotes, maintain consistent indentation
- **Routes**: Route handlers should be concise, with business logic in helper functions
- **Constants**: Define at top of file, use UPPERCASE names
- **Comments**: Add descriptive docstrings for complex functions
- **Types**: Consider adding type hints for function parameters and returns
- **Credentials**: Never hardcode credentials in application code

## Database
- SQLite schema in `schema.sql`
- Data stored in CSV files, accessed through helper functions in app.py