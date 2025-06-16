import sqlalchemy

class DatabaseConnector(object):
	def __init__(self, db_server, database):
		"""
		Define the parameters by which the database_connector can connect a database.
		Parameters:
			db_server: PSRC's db server to export from
			database: PSRC's database to export from
		"""
		try:
			self.db_server = db_server
			self.database = database
			self.connect()
			self.gdb_sde_conn = r'C:\Users\cpeak\OneDrive - Puget Sound Regional Council\Projects\2022\data_portal\data_portal_project\aws-prod-sql.sde'
			self.gdb_sde_conn = r'C:\Users\cpeak\OneDrive - Puget Sound Regional Council\Projects\2022\data_portal\export_without_triangles\elmergeo3.sde'
		except Exception as e:
			print(e.args[0])
			raise


	def connect(self):
		"""
		Make connections to the PSRC database
		"""
		try:
			conn_string = "DRIVER={{ODBC Driver 17 for SQL Server}}; " \
				"SERVER={}; DATABASE={}; trusted_connection=yes".format(
					self.db_server,
					self.database)
			engine = sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect=%s" % conn_string)
			self.sql_conn = engine
		except Exception as e:
			print(e.args[0])
			raise