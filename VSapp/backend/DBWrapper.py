from typing import final
from matplotlib import image
import psycopg2
from psycopg2 import pool
from configparser import ConfigParser

import cv2

from Structs import Image, Video
from constants import BASE_PATH

class DBWrapper:

	def __init__(self):
		self.connPool = psycopg2.pool.ThreadedConnectionPool(1,8,database="andreipetre", user='postgres', password='password', host='127.0.0.1', port='5432', options='-c search_path=vsapp,public')

	def open(self):
			conn = self.connPool.getconn()
			cursor = conn.cursor()
			return (conn, cursor)

	def close(self, conn, cursor):
		cursor.close()
		self.connPool.putconn(conn)

	def get_users(self):
		(conn, cursor) = self.open()
		try:
			cursor.execute(''' SELECT * FROM "Users"; ''')
			result = cursor.fetchall()
			conn.commit()
			return result
		finally:
			self.close(conn, cursor)


	def get_videos(self, id_user):
		(conn, cursor) = self.open()
		try:
			cursor.execute(f''' 
				SELECT * FROM "Videos" 
				left join "Thumbnails" on "Thumbnails"."Id" = "Videos"."IdThumbnail"
				left join "Users" on "Users"."Id" = "Videos"."IdUser"
				WHERE "IdUser" = {id_user}
			; ''')
			result = cursor.fetchall()
			conn.commit()
			return result
		finally:
			self.close(conn, cursor)
	
	def get_images(self, id_user):
		(conn, cursor) = self.open()
		try:
			cursor.execute(f''' 
				SELECT * FROM "Images" 
				left join "Users" on "Users"."Id" = "Images"."IdUser"
				WHERE "IdUser" = {id_user} 
				; 
			''')
			result = cursor.fetchall()
			conn.commit()
			return result
		finally:
			self.close(conn, cursor)

	def get_image_address(self, id_image:int):
		image = self.get_image(id_image)
		return f"{BASE_PATH}{image[1]}" 
	def get_thumbnail_address(self, IdThumbnail:int):
		thumbnail = self.get_thumbnail(IdThumbnail)
		return f"{BASE_PATH}{thumbnail[1]}" 
	def get_video_address(self, IdVideo:int) -> str:
		video = self.get_video(IdVideo)
		return f"{BASE_PATH}{video[1]}" 

	def get_image(self, id_image:int):
		(conn, cursor) = self.open()
		try:
			cursor.execute('SELECT * FROM "Images" where "Images"."Id" = '+str(id_image))
			result = cursor.fetchone()
			return result
		finally:
			self.close(conn, cursor)

	def get_thumbnail(self, IdThumbnail:int):
		(conn, cursor) = self.open()
		try:
			cursor.execute('SELECT * FROM "Thumbnails" where "Thumbnails"."Id" = '+str(IdThumbnail))
			result = cursor.fetchone()
			return result
		finally:
			self.close(conn, cursor)

	def get_video(self, IdVideo:int):
		(conn, cursor) = self.open()
		try:
			cursor.execute('SELECT * FROM "Videos" left join "Thumbnails" on "Thumbnails"."Id" = "Videos"."IdThumbnail" where "Videos"."Id" = '+str(IdVideo))
			result = cursor.fetchone()
			return result
		finally:
			self.close(conn, cursor)


	def get_network_videos(self, id_user):
		images_ids_dict = []
		videos = self.get_videos(id_user)
		for i in range(len(videos)):
			images_ids_dict.append( Video(videos[i][0], videos[i][6], videos[i][10], videos[i][3]).__dict__)

		return images_ids_dict

	def get_network_images(self, id_user):
		images_ids_dict = []
		images = self.get_images(id_user)
		for i in range(len(images)):
			images_ids_dict.append( Image(images[i][0], images[i][5]).__dict__)

		return images_ids_dict

	def get_images_index(self):
		(conn, cursor) = self.open()
		try:
			cursor.execute('SELECT count(*) FROM "Images" ')
			result = cursor.fetchone()
			return result
		finally:
			self.close(conn, cursor)

	def get_thumbnail_index(self):
		(conn, cursor) = self.open()
		try:
			cursor.execute('SELECT count(*) FROM "Thumbnails" ')
			result = cursor.fetchone()
			return result
		finally:
			self.close(conn, cursor)

	def get_videos_index(self):
		(conn, cursor) = self.open()
		try:
			cursor.execute('SELECT count(*) FROM "Videos" ')
			result = cursor.fetchone()
			return result
		finally:
			self.close(conn, cursor)



	def save_image(self, index, fileAddress, idUser, width, height, url):
		(conn, cursor) = self.open()
		try:
			cursor.execute(f'''
			
				INSERT INTO "Images" ("Id", "ImageAddress", "IdUser", "Height", "Width", "URL")
				VALUES({index},'{fileAddress}',{idUser}, {height}, {width}, '{url}') 
				RETURNING "Images"."Id";
			
			''' )
			conn.commit()
			result = cursor.fetchone()
			return result[0]
		finally:
			self.close(conn, cursor)
	

	def save_thumbnail(self, index, thumbnail_address, thumbnail_url):
		(conn, cursor) = self.open()
		try:
			cursor.execute(f'''
			
				INSERT INTO "Thumbnails" ("Id", "ThumbnailAddress", "ThumbnailUrl")
				VALUES({index},'{thumbnail_address}','{thumbnail_url}') 
				RETURNING "Thumbnails"."Id";
			
			''' )
			conn.commit()
			result = cursor.fetchone()
			return result[0]
		finally:
			self.close(conn, cursor)

	def save_video(self, index, fileAddress, idUser, duration, width, height, url, thumbnail_id):
		(conn, cursor) = self.open()
		try:
			cursor.execute(f'''
			
				INSERT INTO "Videos" ("Id", "ImageAddress", "IdUser", "Height", "Width", "URL")
				VALUES({index},'{fileAddress}',{idUser}, {height}, {width}, '{url}', {thumbnail_id}) 
				RETURNING "Images"."Id";
			
			''' )
			conn.commit()
			result = cursor.fetchone()
			return result[0]
		finally:
			self.close(conn, cursor)


	def delete_image(self, id_image:int):
		(conn, cursor) = self.open()
		try:
			cursor.execute(f'''
			
				DELETE FROM "Images" 
				WHERE "Images"."Id" = {id_image};
				RETURNING count(*) "Images"
			
			''' )
			conn.commit()
			result = cursor.fetchone()
			if result == None:
				return "No rows deleted"
			return result
		finally:
			self.close(conn, cursor)

	def delete_video(self, id_thumbnail):
		(conn, cursor) = self.open()
		try:

			#we delete the thumbnail and the delete cascade deletes the video row
			cursor.execute(f'''
			
				DELETE FROM "Thumbnails" 
				WHERE "Thumbnails"."Id" = {id_thumbnail} 
				RETURNING *;

			''' )
			conn.commit()
			result = cursor.fetchone()
			if result == None:
				return "No rows deleted"
			return result
		finally:
			self.close(conn, cursor)
		

db = DBWrapper()
#db.connPool._closeall()








