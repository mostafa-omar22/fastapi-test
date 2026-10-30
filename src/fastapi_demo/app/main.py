from typing import Optional
import os

from dotenv import load_dotenv

from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row
import time

load_dotenv() # this will load the .env file and make the variables available in the environment
db_password = os.getenv("DB_PASSWORD")

while True:# this will keep trying to connect to the database until it succeeds, this is useful when the database is not ready yet.
    try:
        conn = psycopg.connect(host="localhost", dbname="fastapi-demo", user="postgres", password=db_password, row_factory=dict_row)
        curror = conn.cursor()
        print("Database connection was successful")
        break
    except psycopg.Error as e:
        print("Error connecting to the database:", e)
        time.sleep(5)  # Wait for 5 seconds before retrying

class Post(BaseModel): # this is a pydantic model that will be used to validate the request body, without it we cannot validate the values of the request body.
    title: str
    content: str
    published: bool = True # this defaultes the value to true
    
app = FastAPI() # create an instance of the FastAPI class, this will be used to create the API endpoints.
        
@app.get("/posts")
def get_posts():
    curror.execute("""SELECT * FROM posts;""")
    posts = curror.fetchall()
    conn.commit() # this will commit the changes to the database, without it the changes will not be saved.
    return {"posts": posts}

@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    curror.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *;""", (post.title, post.content, post.published))
    new_post = curror.fetchone()
    conn.commit()
    return {"new_post": new_post}

@app.get("/posts/{id}")
def get_post(id: int):
    curror.execute("""SELECT * FROM posts WHERE id = %s;""", (id,))
    post = curror.fetchone()
    if post:
        return {"post_detail": post}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} not found")

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):
    try:
        curror.execute("""DELETE FROM posts WHERE id = %s;""", (id,))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} not found")    

@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    post_dict = post.model_dump()
    try:
        curror.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING *;""", (post_dict['title'], post_dict['content'], post_dict['published'], id))
        updated_post = curror.fetchone()
        conn.commit()
        return {"updated_post": updated_post}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} not found")    