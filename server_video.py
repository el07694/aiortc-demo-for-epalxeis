import av.logging
restore_default_callback = lambda *args: args
av.logging.restore_default_callback = restore_default_callback
av.logging.set_level(av.logging.ERROR)
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, QThread
from calls import Ui_MainWindow
from aiohttp import web
from aiohttp.web_runner import GracefulExit
from aiortc.mediastreams import MediaStreamTrack,MediaStreamError
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRelay
import av
import pyaudio
from pydub import AudioSegment,generators
import asyncio
import json
import os
from multiprocessing import Process, Queue, Pipe, freeze_support
from queue import Queue as Simple_Queue
import sys
import threading
import fractions
import requests
from PIL import Image
import ssl
ssl._create_default_https_context = ssl._create_unverified_context 
from pyngrok import ngrok, conf
from pyngrok.conf import PyngrokConfig

from pygrabber.dshow_graph import FilterGraph
import traceback

#conf.set_default(PyngrokConfig(region="au", ngrok_path=os.path.abspath("ngrok.exe")))
ngrok.set_auth_token("1kxaH4jyih9qTuyTBE0V6bzYbnq_nVaCNY5wwUriYY5oiLDr")
import socket

import uuid

class Main:
	def __init__(self,ngrok_url):
		self.app = QtWidgets.QApplication(sys.argv)
		self.MainWindow = QtWidgets.QMainWindow()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self.MainWindow)
		self.MainWindow.showMaximized()
		
		
		self.ui.server_frame.hide()
		self.ui.client_1_frame.hide()
		self.ui.client_2_frame.hide()
		self.ui.client_3_frame.hide()
		
		self.ui.ngrok_url.setText(ngrok_url)

		self.mother_pipe, self.child_pipe = Pipe()
		self.call_queues = [Queue(),Queue(),Queue()]
		self.emitter = Emitter(self.mother_pipe)
		
		self.emitter.call_1_offering.connect(lambda name,surname:self.new_call(1,name,surname))
		self.emitter.call_1_status.connect(lambda status:self.call_status(1,status))
		
		self.emitter.call_2_offering.connect(lambda name,surname:self.new_call(2,name,surname))
		self.emitter.call_2_status.connect(lambda status:self.call_status(2,status))

		self.emitter.call_3_offering.connect(lambda name,surname:self.new_call(3,name,surname))
		self.emitter.call_3_status.connect(lambda status:self.call_status(3,status))
		
		self.emitter.server_web_camera_packet.connect(lambda pil_image:self.display_video_frame(0,pil_image[0]))
		self.emitter.client_1_web_camera_packet.connect(lambda pil_image:self.display_video_frame(1,pil_image[0]))
		self.emitter.client_2_web_camera_packet.connect(lambda pil_image:self.display_video_frame(2,pil_image[0]))
		self.emitter.client_3_web_camera_packet.connect(lambda pil_image:self.display_video_frame(3,pil_image[0]))
		self.emitter.hide_server_web_camera.connect(lambda:self.hide_server_web_camera())
		self.emitter.start()		
		
		self.aiohttp_server = WebRtcServer(self.child_pipe,self.call_queues)
		self.aiohttp_server.start()
		
		self.MainWindow.closeEvent = lambda event:self.closeEvent(event)
		
		sys.exit(self.app.exec_())

	def new_call(self,call_number,name,surname):
		if call_number == 1:
			self.ui.client_1_frame.show()
			self.ui.client_1_label.show()
			self.ui.client_1_label.setText("Τηλεφωνική κλήση από: "+str(name)+" "+str(surname))
			self.ui.client_1_accept.show()
			self.ui.client_1_accept.clicked.connect(lambda state:self.answer_call(1,state))
			self.ui.client_1_video.clear()
			self.ui.client_1_reject.show()
			self.ui.client_1_reject.clicked.connect(lambda state:self.reject_call(1,state))
			self.ui.client_1_stop.hide()
		elif call_number == 2:
			self.ui.client_2_frame.show()
			self.ui.client_2_label.show()
			self.ui.client_2_label.setText("Τηλεφωνική κλήση από: "+str(name)+" "+str(surname))
			self.ui.client_2_accept.show()
			self.ui.client_2_accept.clicked.connect(lambda state:self.answer_call(2,state))
			self.ui.client_2_video.clear()
			self.ui.client_2_reject.show()
			self.ui.client_2_reject.clicked.connect(lambda state:self.reject_call(2,state))
			self.ui.client_2_stop.hide()
		else:
			self.ui.client_3_frame.show()
			self.ui.client_3_label.show()
			self.ui.client_3_label.setText("Τηλεφωνική κλήση από: "+str(name)+" "+str(surname))
			self.ui.client_3_accept.show()
			self.ui.client_3_accept.clicked.connect(lambda state:self.answer_call(3,state))
			self.ui.client_3_video.clear()
			self.ui.client_3_reject.show()
			self.ui.client_3_reject.clicked.connect(lambda state:self.reject_call(3,state))
			self.ui.client_3_stop.hide()
				
	def answer_call(self,call_number,state):
		if call_number == 1:
			self.ui.client_1_accept.hide()
			self.ui.client_1_reject.hide()
			self.ui.client_1_stop.show()
			self.ui.client_1_stop.clicked.connect(lambda state:self.end_call(1,state))
			self.call_queues[0].put({"type":"call-1","call":"answer"})
			
			self.call_1_timer = QtCore.QTimer()
			self.call_1_timer.timeout.connect(lambda:self.end_call(1,None))
			self.call_1_timer.setSingleShot(True)
			self.call_1_timer.start(7000)
		elif call_number == 2:
			self.ui.client_2_accept.hide()
			self.ui.client_2_reject.hide()
			self.ui.client_2_stop.show()
			self.ui.client_2_stop.clicked.connect(lambda state:self.end_call(2,state))
			self.call_queues[1].put({"type":"call-2","call":"answer"})
			
			self.call_2_timer = QtCore.QTimer()
			self.call_2_timer.timeout.connect(lambda:self.end_call(2,None))
			self.call_2_timer.setSingleShot(True)
			self.call_2_timer.start(7000)
		elif call_number == 3:
			self.ui.client_3_accept.hide()
			self.ui.client_3_reject.hide()
			self.ui.client_3_stop.show()
			self.ui.client_3_stop.clicked.connect(lambda state:self.end_call(3,state))
			self.call_queues[2].put({"type":"call-3","call":"answer"})
			
			self.call_3_timer = QtCore.QTimer()
			self.call_3_timer.timeout.connect(lambda:self.end_call(3,None))
			self.call_3_timer.setSingleShot(True)
			self.call_3_timer.start(7000)
		
	def reject_call(self,call_number,state):
		if call_number == 1:
			self.ui.client_1_frame.hide()
			self.ui.client_1_label.hide()
			self.ui.client_1_accept.hide()
			self.ui.client_1_reject.hide()
			self.ui.client_1_stop.hide()
			self.call_queues[0].put({"type":"call-1","call":"reject"})
		elif call_number == 2:
			self.ui.client_2_frame.hide()
			self.ui.client_2_label.hide()
			self.ui.client_2_accept.hide()
			self.ui.client_2_reject.hide()
			self.ui.client_2_stop.hide()
			self.call_queues[1].put({"type":"call-2","call":"reject"})
		elif call_number == 3:
			self.ui.client_3_frame.hide()
			self.ui.client_3_label.hide()
			self.ui.client_3_accept.hide()
			self.ui.client_3_reject.hide()
			self.ui.client_3_stop.hide()
			self.call_queues[2].put({"type":"call-3","call":"reject"})
		
	def end_call(self,call_number,state):
		if call_number == 1:
			self.ui.client_1_frame.hide()
			self.ui.client_1_label.hide()
			self.ui.client_1_accept.hide()
			self.ui.client_1_reject.hide()
			self.ui.client_1_stop.hide()
			self.call_queues[0].put({"type":"call-1","call":"end"})
		elif call_number == 2:
			self.ui.client_2_frame.hide()
			self.ui.client_2_label.hide()
			self.ui.client_2_accept.hide()
			self.ui.client_2_reject.hide()
			self.ui.client_2_stop.hide()
			self.call_queues[1].put({"type":"call-2","call":"end"})
		if call_number == 3:
			self.ui.client_3_frame.hide()
			self.ui.client_3_label.hide()
			self.ui.client_3_accept.hide()
			self.ui.client_3_reject.hide()
			self.ui.client_3_stop.hide()
			self.call_queues[2].put({"type":"call-3","call":"end"})
	
	def call_status(self,call_number,status):
		if status == "closed-by-client" or status == "closed-by-server":
			if call_number == 1:
				self.ui.client_1_frame.hide()
				self.ui.client_1_label.hide()
				self.ui.client_1_accept.hide()
				self.ui.client_1_reject.hide()
				self.ui.client_1_stop.hide()
			elif call_number == 2:
				self.ui.client_2_frame.hide()
				self.ui.client_2_label.hide()
				self.ui.client_2_accept.hide()
				self.ui.client_2_reject.hide()
				self.ui.client_2_stop.hide()
			elif call_number == 3:
				self.ui.client_3_frame.hide()
				self.ui.client_3_label.hide()
				self.ui.client_3_accept.hide()
				self.ui.client_3_reject.hide()
				self.ui.client_3_stop.hide()
	
	def display_video_frame(self,call_id,pil_image):
		if call_id == 0: #0 for self video
			self.ui.server_frame.show()
			pixmap = self.pil2pixmap(pil_image)
			self.ui.server_video.setPixmap(pixmap)
			self.ui.server_video.show()
		elif call_id == 1:
			if pil_image is None:
				return self.end_call(1,None)
			pixmap = self.pil2pixmap(pil_image)
			self.ui.client_1_video.setPixmap(pixmap)
			self.ui.client_1_video.show()
			self.call_1_timer.stop()
			self.call_1_timer = QtCore.QTimer()
			self.call_1_timer.timeout.connect(lambda:self.end_call(1,None))
			self.call_1_timer.setSingleShot(True)
			self.call_1_timer.start(7000)
		if call_id == 2:
			if pil_image is None:
				return self.end_call(2,None)
			pixmap = self.pil2pixmap(pil_image)
			self.ui.client_2_video.setPixmap(pixmap)
			self.ui.client_2_video.show()
			self.call_2_timer.stop()
			self.call_2_timer = QtCore.QTimer()
			self.call_2_timer.timeout.connect(lambda:self.end_call(2,None))
			self.call_2_timer.setSingleShot(True)
			self.call_2_timer.start(7000)
		if call_id == 3:
			if pil_image is None:
				return self.end_call(3,None)
			pixmap = self.pil2pixmap(pil_image)
			self.ui.client_3_video.setPixmap(pixmap)
			self.ui.client_3_video.show()
			self.call_3_timer.stop()
			self.call_3_timer = QtCore.QTimer()
			self.call_3_timer.timeout.connect(lambda:self.end_call(3,None))
			self.call_3_timer.setSingleShot(True)
			self.call_3_timer.start(7000)

	def pil2pixmap(self, im):
		if im.mode == "RGB":
			r, g, b = im.split()
			im = Image.merge("RGB", (b, g, r))
		elif  im.mode == "RGBA":
			r, g, b, a = im.split()
			im = Image.merge("RGBA", (b, g, r, a))
		elif im.mode == "L":
			im = im.convert("RGBA")
		# Bild in RGBA konvertieren, falls nicht bereits passiert
		im2 = im.convert("RGBA")
		data = im2.tobytes("raw", "RGBA")
		qim = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_ARGB32)
		pixmap = QtGui.QPixmap.fromImage(qim)
		return pixmap

	def hide_server_web_camera(self):
		self.ui.server_video.clear()
		self.ui.server_frame.hide()

	def closeEvent(self,event):
		#try:
		#	response = requests.post('http://192.168.1.188:8080/shutdown', timeout=30)
		#except:
		#	pass
		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		#si.wShowWindow = subprocess.SW_HIDE # default
		subprocess.call('taskkill /f /im ngrok.exe', startupinfo=si)
		self.aiohttp_server.terminate()
		event.accept()

class Emitter(QThread):
	call_1_offering = pyqtSignal(str,str)
	call_1_status = pyqtSignal(str)

	call_2_offering = pyqtSignal(str,str)
	call_2_status = pyqtSignal(str)

	call_3_offering = pyqtSignal(str,str)
	call_3_status = pyqtSignal(str)
	
	hide_server_web_camera = pyqtSignal()

	server_web_camera_packet = pyqtSignal(list)
	client_1_web_camera_packet = pyqtSignal(list)
	client_2_web_camera_packet = pyqtSignal(list)
	client_3_web_camera_packet = pyqtSignal(list)
	
	def __init__(self, from_process: Pipe):
		super().__init__()
		self.data_from_process = from_process
		
	def run(self):
		while True:
			data = self.data_from_process.recv()
			if data["type"]=="call_1_offering":
				self.call_1_offering.emit(data["name"],data["surname"])
			elif data["type"] == "call-1-status":
				self.call_1_status.emit(data["status"])
			elif data["type"]=="call_2_offering":
				self.call_2_offering.emit(data["name"],data["surname"])
			elif data["type"] == "call-2-status":
				self.call_2_status.emit(data["status"])
			elif data["type"]=="call_3_offering":
				self.call_3_offering.emit(data["name"],data["surname"])
			elif data["type"] == "call-3-status":
				self.call_3_status.emit(data["status"])
			elif data["type"] == "server-web-camera-frame":
				self.server_web_camera_packet.emit(data["pil_image"])
			elif data["type"] == "client-1-web-camera-frame":
				self.client_1_web_camera_packet.emit(data["pil_image"])
			elif data["type"] == "client-2-web-camera-frame":
				self.client_2_web_camera_packet.emit(data["pil_image"])
			elif data["type"] == "client-3-web-camera-frame":
				self.client_3_web_camera_packet.emit(data["pil_image"])	   
			elif data["type"] == "hide_server_web_camera":
				self.hide_server_web_camera.emit()

class WebRtcServer(Process):
	def __init__(self, to_emitter, call_queues):
		super().__init__()
		
		self.to_emitter = to_emitter
		self.call_queues = call_queues
		
		if getattr(sys, 'frozen', False):
			self.ROOT = os.path.dirname(sys.executable)
		elif __file__:
			self.ROOT = os.path.dirname(__file__)
		
		self.pcs = {}
		self.webcam = None
		self.server_audio_stream_offer = None
		self.server_audio_blackholde = None
		self.server_video_stream_offer = None
		self.server_video_track = None
		self.server_video_blackholde = None
			
	def run(self):
		hostname = socket.gethostname()
		ip_address = socket.gethostbyname(hostname)
		self.app = web.Application()
		self.app.on_shutdown.append(self.on_shutdown)
		self.app.router.add_get("/", self.index)
		self.app.router.add_get("/video_calls.js", self.javascript)
		self.app.router.add_post("/offer", self.offer)
		self.app.router.add_get("/signal.mp3", self.mp3)
		self.app.router.add_get("/telephone-call.ico", self.favicon)
		self.app.router.add_post("/shutdown", self.shutdown_aiohttp)
		web.run_app(self.app, access_log=None, host=str(ip_address), port=80, ssl_context=None,keepalive_timeout=60.0,backlog=300)

	def get_available_cameras(self):
		devices = FilterGraph().get_input_devices()
		available_cameras = {}
		for device_index, device_name in enumerate(devices):
			available_cameras[device_index] = device_name
		return available_cameras

	def create_local_tracks(self):
		options = {"framerate": "30", "video_size": "640x480"}
		camera_name = "video="+self.get_available_cameras()[0]
		self.webcam = MediaPlayer(camera_name, format='dshow', options=options)
		relay = MediaRelay()
		return relay.subscribe(self.webcam.video)

	async def index(self,request):
		content = open(os.path.join(self.ROOT, "index.html"), encoding="utf8").read()
		return web.Response(content_type="text/html", text=content)

	async def javascript(self,request):
		content = open(os.path.join(self.ROOT, "video_calls.js"), encoding="utf8").read()
		return web.Response(content_type="application/javascript", text=content)

	async def mp3(self,request):
		return web.FileResponse(os.path.join(self.ROOT, "signal.mp3"))
		
	async def favicon(self,request):
		return web.FileResponse(os.path.join(self.ROOT, "telephone-call.ico"))
		
	async def offer(self,request):	
		params = await request.json()
		
		peer_connection = {
			"name":params["name"],
			"surname":params["surname"],
			"pc":None,
			"is_closed":False,
			"dc":None,
			"uid":uuid.uuid4(),
			"audio_track":None,
			"audio_track_for_local_use":None,
			"audio_blackhole":None,
			"video_track":None,
			"video_track_for_local_use":None,
			"video_blackhole":None,
			"offer_in_progress":True,
			"call_answered":False,
			"manage_call_end_thread":None,
			"stop_in_progress":False,
			"call_number":None
		}
		
		if len(list(self.pcs.keys())) == 3:
			return web.Response(content_type="application/json",text=json.dumps({"sdp": "", "type": ""}))
				
		
		reserved_call_numbers = list(self.pcs.keys())
		
		if 1 not in reserved_call_numbers:
			call_number = 1
		elif 2 not in reserved_call_numbers:
			call_number = 2
		else:
			call_number = 3
		
		peer_connection["call_number"] = call_number
		self.pcs[call_number] = peer_connection

		hear_call_intro_thread = threading.Thread(target=self.hear_call_intro,args=(call_number,))
		hear_call_intro_thread.start()

		
		if call_number == 1:
			self.to_emitter.send({"type":"call_1_offering","name":peer_connection["name"],"surname":peer_connection["surname"]})
			data_from_mother = self.call_queues[0]
		elif call_number == 2:
			self.to_emitter.send({"type":"call_2_offering","name":peer_connection["name"],"surname":peer_connection["surname"]})
			data_from_mother = self.call_queues[1]
		else:
			self.to_emitter.send({"type":"call_3_offering","name":peer_connection["name"],"surname":peer_connection["surname"]})
			data_from_mother = self.call_queues[2]

		timer = 0
		while(timer<30 and data_from_mother.qsize()==0 and self.pcs[call_number]["call_answered"] == False):
			if request.transport is None or request.transport.is_closing():
				try:
					request.transport.close()
				except:
					pass
				pass
				break
			timer+=0.1
			await asyncio.sleep(0.1)
		self.pcs[call_number]["call_answered"] = True
		if data_from_mother.qsize() == 0:
			#reject offer
			while not data_from_mother.empty():
				data_from_mother.get()
			if call_number == 1:
				self.to_emitter.send({"type":"call-1-status","status":"closed-by-server"})
			elif call_number == 2:
				self.to_emitter.send({"type":"call-2-status","status":"closed-by-server"})
			else:
				self.to_emitter.send({"type":"call-3-status","status":"closed-by-server"})
			await self.stop_peer_connection(peer_connection["uid"])
			return web.Response(content_type="application/json",text=json.dumps({"sdp": "", "type": ""}))
		else:
			data = data_from_mother.get()
			if (data["type"] == "call-1" and data["call"] == "answer") or (data["type"] == "call-2" and data["call"] == "answer") or (data["type"] == "call-3" and data["call"] == "answer"):
				while not data_from_mother.empty():
					data_from_mother.get()

				self.pcs[call_number]["pc"] = RTCPeerConnection()


				@self.pcs[call_number]["pc"].on("connectionstatechange")
				async def on_connectionstatechange():
					if self.pcs[call_number]["pc"].connectionState == "failed":
						await self.stop_peer_connection(peer_connection["uid"])

				@self.pcs[call_number]["pc"].on("datachannel")
				async def on_datachannel(channel):
					self.pcs[call_number]["dc"] = channel
					try:
						channel.send('{"type":"uid","uid":"'+str(peer_connection["uid"])+'"}')
					except:
						pass
						
					counter = 1
					for pc_i_call_number in self.pcs:
						try:
							if pc_i_call_number != call_number:
								pc_i = self.pcs[pc_i_call_number]
								channel.send('{"type":"new-client","uid":"'+str(pc_i["uid"])+'","name":"'+str(pc_i["name"])+'","surname":"'+str(pc_i["surname"])+'"}')
								counter += 1
						except:
							pass
					
												

					@channel.on("message")
					async def on_message(message):
						message = json.loads(message)
						if message["type"] == "disconnected":
							await self.stop_peer_connection(peer_connection["uid"])

				
				#audio from server to client
				if self.server_audio_stream_offer == None:
					self.server_audio_stream_offer = Server_Audio_Stream_Offer()
				self.pcs[call_number]["pc"].addTrack(self.server_audio_stream_offer)
				
				#video from server to client
				if self.server_video_stream_offer == None:
					self.server_video_stream_offer = self.create_local_tracks()
				self.pcs[call_number]["pc"].addTrack(self.server_video_stream_offer)
									
				#video from server attach to QLabel
				if self.server_video_track == None:
					self.server_video_track = WebCamera(self.server_video_stream_offer,self.to_emitter)
				if self.server_video_blackholde == None:
					self.server_video_blackholde = MediaBlackhole()
					self.server_video_blackholde.addTrack(self.server_video_track)
					await self.server_video_blackholde.start()
				

				
				@self.pcs[call_number]["pc"].on("track")
				async def on_track(track):	
					if track.kind == "audio":
						self.pcs[call_number]["audio_track"] = track
						#audio from client (server use)
						self.pcs[call_number]["audio_track_for_local_use"] = ClientTrack(track,self,self.to_emitter)
						self.pcs[call_number]["audio_blackhole"] = MediaBlackhole()
						self.pcs[call_number]["audio_blackhole"].addTrack(self.pcs[call_number]["audio_track_for_local_use"])
						await self.pcs[call_number]["audio_blackhole"].start()
					else:
						self.pcs[call_number]["video_track"] = track
						#video from client (server use)
						self.pcs[call_number]["video_track_for_local_use"] = ClientWebCamera(track,self.to_emitter,call_number,self)
						self.pcs[call_number]["video_blackhole"] = MediaBlackhole()
						self.pcs[call_number]["video_blackhole"].addTrack(self.pcs[call_number]["video_track_for_local_use"])
						await self.pcs[call_number]["video_blackhole"].start()
					
				offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
				
				# handle offer
				await self.pcs[call_number]["pc"].setRemoteDescription(offer)

				# send answer
				answer = await self.pcs[call_number]["pc"].createAnswer()
				await self.pcs[call_number]["pc"].setLocalDescription(answer)

				loop = asyncio.get_event_loop()
				task = asyncio.ensure_future(self.manage_call_end(loop,peer_connection["uid"]))
				self.pcs[call_number]["manage_call_end_thread"] = task
				
				return web.Response(content_type="application/json",text=json.dumps({"sdp": self.pcs[call_number]["pc"].localDescription.sdp, "type": self.pcs[call_number]["pc"].localDescription.type}))
			else:
				#reject call
				while not data_from_mother.empty():
					data_from_mother.get()
				if call_number == 1:
					self.to_emitter.send({"type":"call-1-status","status":"closed-by-server"})
				elif call_number == 2:
					self.to_emitter.send({"type":"call-2-status","status":"closed-by-server"})
				else:
					self.to_emitter.send({"type":"call-3-status","status":"closed-by-server"})
				await self.stop_peer_connection(peer_connection["uid"])
				return web.Response(content_type="application/json",text=json.dumps({"sdp": "", "type": ""}))

	async def stop_peer_connection(self,uid):
		counter = 0
		for pc_call_number in self.pcs.keys():
			if self.pcs[pc_call_number]["uid"] == uid:
				call_number = pc_call_number
				break
				
		if self.pcs[call_number]["pc"] is None:
			try:
				self.pcs[call_number]["offer_in_progress"] = False
				self.pcs[call_number]["call_answered"] = True
			except:
				pass
			
			del self.pcs[call_number]
			return None
		if self.pcs[call_number]["is_closed"]:
			return None
		self.pcs[call_number]["is_closed"] = True
		
		
		data_from_mother = self.call_queues[call_number-1]
		
			
		if self.pcs[call_number]["stop_in_progress"]:
			return None
		else:
			self.pcs[call_number]["stop_in_progress"] = True
		try:
			if self.pcs[call_number]["pc"] is not None:
				try:
					await self.pcs[call_number]["pc"].close()
					del self.pcs[call_number]["pc"]
				except Exception as e:
					pass
			if self.pcs[call_number]["call_answered"] == True:
				try:
					self.pcs[call_number]["dc"].close()
				except:
					pass
			if self.server_audio_stream_offer is not None:
				if len(list(self.pcs.keys())) == 1:
					self.server_audio_stream_offer.stop()
					self.server_audio_stream_offer.stop_offering()
					del self.server_audio_stream_offer
					self.server_audio_stream_offer = None
			try:
				if self.pcs[call_number]["audio_blackhole"] is not None:
					await self.pcs[call_number]["audio_blackhole"].stop()
					self.pcs[call_number]["audio_blackhole"] = None
					del self.pcs[call_number]["audio_blackhole"]
			except:
				pass
			try:
				if self.pcs[call_number]["audio_track_for_local_use"] is not None:
					self.pcs[call_number]["audio_track_for_local_use"].close_full()
					del self.pcs[call_number]["audio_track_for_local_use"]
			except:
				pass
			
			try:
				if len(list(self.pcs.keys())) == 1:
					try:
						self.webcam.video.stop()
						self.server_video_track.stop()
						await self.server_video_blackholde.stop()
						self.server_video_track = None
						self.server_video_blackholde = None
					except:
						pass
			except:
				pass
			if call_number == 1:
				self.to_emitter.send({"type":"call-1-status","status":"closed-by-client"})
			elif call_number == 2:
				self.to_emitter.send({"type":"call-2-status","status":"closed-by-client"})
			else:
				self.to_emitter.send({"type":"call-3-status","status":"closed-by-client"})


			try:
				self.pcs[call_number]["video_track_for_local_use"].stop()
				await self.pcs[call_number]["video_blackhole"].stop()
			except:
				pass
			
			try:
				del self.pcs[call_number]["video_track_for_local_use"]
				del self.pcs[call_number]["video_blackhole"]
			except:
				pass
				
			try:	
				self.pcs[call_number]["call_answered"] = False
			except:
				pass

			try:
				del self.pcs[call_number]["dc"]
			except:
				pass

			try:
				self.pcs[call_number]["offer_in_progress"] = False
				del self.pcs[call_number]["manage_call_end_thread"]
			except:
				pass
			try:
				if len(list(self.pcs.keys())) == 1:
					self.to_emitter.send({"type":"hide_server_web_camera"})
					self.server_video_stream_offer = None
				
				del self.pcs[call_number]["audio_track"]
				del self.pcs[call_number]["video_track"]
			except:
				pass
		except Exception as e:
			pass
			
		while not data_from_mother.empty():
			data_from_mother.get()
			
		del self.pcs[call_number]
				
	def hear_call_intro(self,call_number):
		self.audio_segment = AudioSegment.from_file(r"telephone_calls.mp3").set_frame_rate(44800)
		self.total_duration_milliseconds = len(self.audio_segment)
		self.chunk_number = 0
		self.current_duration_milliseconds = 0
		
		self.p = pyaudio.PyAudio()
		self.output_stream = self.p.open(format=pyaudio.paInt16,channels=2,rate=44800,output=True,frames_per_buffer=int(16384/4))
		self.output_stream.start_stream()
		self.packet_time = 125


		sine_segment = generators.Sine(1000).to_audio_segment()
		sine_segment = sine_segment.set_frame_rate(44800)
		sine_segment = sine_segment[(1000-int(self.packet_time))/2:self.packet_time+(1000-int(self.packet_time))/2]
		self.silent_segment = sine_segment-200

		for pc_call_number in self.pcs:
			if pc_call_number == call_number:
				peer_connection = self.pcs[call_number]
				break

		while(peer_connection["call_answered"]==False):
			if((self.chunk_number+1)*(self.packet_time)<=self.total_duration_milliseconds):
				slice = self.audio_segment[self.chunk_number*(self.packet_time):(self.chunk_number+1)*(self.packet_time)]
			else:
				if((self.chunk_number)*(self.packet_time)<self.current_duration_milliseconds):
					slice = self.audio_segment[self.chunk_number*(self.packet_time):]
				else:
					slice = self.silent_segment
					self.chunk_number = 0
					
			self.output_stream.write(slice.raw_data)
			self.chunk_number += 1

	async def manage_call_end(self,loop,uid):
		for pc_call_number in self.pcs:
			if self.pcs[pc_call_number]["uid"] == uid:
				call_number = pc_call_number
				break
					
		data_from_mother = self.call_queues[call_number-1]
		asyncio.set_event_loop(loop)
		try:
			while(self.pcs[call_number]["offer_in_progress"]):
				qsize = data_from_mother.qsize()
				if qsize == 0:
					await asyncio.sleep(1)
				else:
					data = data_from_mother.get()
					while not data_from_mother.empty():
						_ = data_from_mother.get()
					
					try:
						self.pcs[call_number]["dc"].send('{"type":"closing","uid":\"'+str(uid)+'\"}')
					except:
						pass
					await self.stop_peer_connection(uid)
					break
		except:
			pass
			
	async def on_shutdown(self,app):
		for pc_call_number in self.pcs:
			await self.stop_peer_connection(self.pcs[pc_call_number]["uid"])
		raise GracefulExit()
		
	async def shutdown_aiohttp(self,request):
		await self.on_shutdown(self.app)
		return web.Response(content_type="text/html", text="")

class Server_Audio_Stream_Offer(MediaStreamTrack):
	kind = "audio"

	def __init__(self):
		super().__init__()	# don't forget this!
		
		self.q = Simple_Queue()
		
		self.codec = av.CodecContext.create('pcm_s16le', 'r')
		self.codec.sample_rate = 8000
		self.codec.channels = 2

		self.audio_samples = 0

		self.p = pyaudio.PyAudio()
		self.input_stream = self.p.open(format=pyaudio.paInt16,channels=2,rate=8000,input=True,frames_per_buffer=int(8000*0.020))
		self.input_stream.start_stream()
		
		self.run = True
		
		self.packet_time = 1000*0.020

		sine_segment = generators.Sine(1000).to_audio_segment()
		sine_segment = sine_segment.set_frame_rate(44800)
		sine_segment = sine_segment[(1000-int(self.packet_time))/2:self.packet_time+(1000-int(self.packet_time))/2]
		self.silent_segment = sine_segment-200

		
		self.read_from_microphone_thread = threading.Thread(target=self.read_from_microphone)
		self.read_from_microphone_thread.start()
		
	async def recv(self):
		packet = av.Packet(self.q.get())
		frame = self.codec.decode(packet)[0]
		frame.pts = self.audio_samples
		frame.time_base = fractions.Fraction(1, self.codec.sample_rate)
		self.audio_samples += frame.samples
		return frame

	def read_from_microphone(self):
		while(self.run):
			try:
				in_data = self.input_stream.read(int(8000*0.020),exception_on_overflow = False)			   
				slice = AudioSegment(in_data, sample_width=2, frame_rate=8000, channels=2)
				self.q.put(slice.raw_data)
			except:
				pass

	def stop_offering(self):
		try:
			self.run = False
			self.read_from_microphone_thread.join()
			self.input_stream.stop_stream()
			self.input_stream.close()
		except Exception as e:
			pass

class WebCamera(MediaStreamTrack):
	kind = "video"

	def __init__(self,track,to_emitter):
		super().__init__()	# don't forget this!
		self.track = track
		self.to_emitter = to_emitter
		
	async def recv(self):
		frame = await self.track.recv()
		pil_image = frame.to_image()
		self.to_emitter.send({"type":"server-web-camera-frame","pil_image":[pil_image]})
		return None

class ClientWebCamera(MediaStreamTrack):
	kind = "video"

	def __init__(self,track,to_emitter,call_number,parent_self):
		super().__init__()	# don't forget this!
		self.track = track
		self.to_emitter = to_emitter
		self.call_number = call_number
		self.parent_self = parent_self
		
	async def recv(self):
		try:
			frame = await self.track.recv()
			pil_image = frame.to_image()
			if self.call_number == 1:
				self.to_emitter.send({"type":"client-1-web-camera-frame","pil_image":[pil_image]})
			elif self.call_number == 2:
				self.to_emitter.send({"type":"client-2-web-camera-frame","pil_image":[pil_image]})
			else:
				self.to_emitter.send({"type":"client-3-web-camera-frame","pil_image":[pil_image]})
			return None
		except:
			raise MediaStreamError
			
class ClientTrack(MediaStreamTrack):
	kind = "audio"

	def __init__(self, track,parent_self,to_emitter):
		super().__init__()
		self.track = track
		self.parent_self = parent_self
		self.to_emitter = to_emitter
		self.q = Simple_Queue()
		self.p = pyaudio.PyAudio()
		self.output_stream = self.p.open(format=pyaudio.paInt16,channels=2,rate=44800,output=True,frames_per_buffer=int(16384/4))
		self.output_stream.start_stream()
		
		self.run = True
		self.hear_client_thread = threading.Thread(target=self.hear_client)
		self.hear_client_thread.start()
		
	async def recv(self):
		# Get a new PyAV frame

		try:
			frame = await self.track.recv()
			self.q.put(frame)
		except:
			self.q.put(None)
			if self.run:
				self.close_full()
				raise MediaStreamError
				return None
			else:
				raise MediaStreamError
				return None
		
		
	def hear_client(self):
		while(self.run):
			frame = self.q.get()
			if frame is None:
				break
			packet_bytes = frame.to_ndarray().tobytes()
			self.output_stream.write(packet_bytes)
		
	def close_full(self):
		self.run = False
		self.hear_client_thread.join()
		self.output_stream.stop_stream()
		self.output_stream.close()

if __name__ == "__main__":
	if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
		freeze_support()
	si = subprocess.STARTUPINFO()
	si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	#si.wShowWindow = subprocess.SW_HIDE # default
	subprocess.call('taskkill /f /im ngrok.exe', startupinfo=si)
	hostname = socket.gethostname()
	ip_address = socket.gethostbyname(hostname)
	tunnel = ngrok.connect(str(ip_address), "http","host_header:rewrite")
	program = Main(tunnel.public_url)