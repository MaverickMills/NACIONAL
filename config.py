class Config:  # crea una clase para guardar configuraciones

    # ruta de la base de datos SQLite
    SQLALCHEMY_DATABASE_URI = "sqlite:///sistema.db"

    # desactiva mensajes innecesarios
    SQLALCHEMY_TRACK_MODIFICATIONS = False
