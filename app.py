from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import time
import cv2
import threading
import queue
import gemini_api
import utils

app = Flask(__name__)

genai_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=genai_api_key)
segment_queue = queue.Queue()

@app.route('/upload_video', methods=['POST'])
def upload_video():
    file = request.files['video']
    timestamp = utils.getDateTime()
    filename = f"./Cache_Recordings/FILE-{timestamp}.mp4"
    file.save(filename)
    segment_queue.put(filename)
    return jsonify({"message": "Video uploaded successfully"}), 200

@app.route('/response', methods=['GET'])
def get_response():
    response_file = 'response.txt'
    if os.path.exists(response_file):
        with open(response_file, 'r') as file:
            response = file.read()
        return response, 200
    return jsonify({"message": "No response available"}), 404

def process_segments():
    while True:
        dateTime = utils.getDateTime()
        localFilename = segment_queue.get()
        if localFilename is None:
            break

        try:
            cloudFilePath = gemini_api.uploadFileToCloud(filename=localFilename)
            response = gemini_api.GetModelResponseFromVideo(gemini_api.GeneratePromptForVideo(dateTime), cloudFilePath, genai_api_key)
        except Exception as e:
            response = "Error occurred during processing."
        finally:
            gemini_api.deleteVideoFromLocal(localFilename)
            gemini_api.deleteVideoFromCloud(cloudFilePath)

        gemini_api.generateInteractiveSpeech(response)

if __name__ == "__main__":
    threading.Thread(target=process_segments, daemon=True).start()
    app.run(debug=True)
