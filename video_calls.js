// peer connection
var pc = null;
var total_clients_audio = 0;
var total_clients_video = 0;
var have_server_video = false;
var have_server_audio = false;

var local_call_number = null;
var clients_pc = [];

var closing = false


var controller = null;
var signal;

var local_stream = {"audio":null,"video":null};
var stream_client_1 = {"audio":null,"video":null};
var stream_client_2 = {"audio":null,"video":null};
var stream_client_3 = {"audio":null,"video":null};

function createLocalPeerConnection(client_call_number,client_name,client_surname){
	var config = {
		sdpSemantics: 'unified-plan',
		iceServers: [{urls: ['stun:stun.l.google.com:19302']}]
	};
	

	clients_pc.push(new RTCPeerConnection(config));

	clients_pc[clients_pc.length-1].addEventListener('track', function(evt) {
		
		console.log(client_call_number);
		if (evt.track.kind == 'audio'){
			if (local_call_number == 1){
				if (client_call_number == 2){
					document.getElementById('client-audio-2').srcObject = evt.streams[0];
					stream_client_2.audio = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-audio-3').srcObject = evt.streams[0];
					stream_client_3.audio = evt.streams[0];
				}
			}else if (local_call_number == 2){
				if (client_call_number == 1){
					document.getElementById('client-audio-2').srcObject = evt.streams[0];
					stream_client_2.audio = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-audio-3').srcObject = evt.streams[0];
					stream_client_3.audio = evt.streams[0];
				}
			}else{
				if (client_call_number == 1){
					document.getElementById('client-audio-2').srcObject = evt.streams[0];
					stream_client_2.audio = evt.streams[0];
				}else if (client_call_number == 2){
					document.getElementById('client-audio-3').srcObject = evt.streams[0];
					stream_client_3.audio = evt.streams[0];
				}
			}
		}else{
			if (local_call_number == 1){
				if (client_call_number == 2){
					document.getElementById('client-video-2').srcObject = evt.streams[0];
					stream_client_2.video = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-video-3').srcObject = evt.streams[0];
					stream_client_3.video = evt.streams[0];
				}
			}else if (local_call_number == 2){
				if (client_call_number == 1){
					document.getElementById('client-video-2').srcObject = evt.streams[0];
					stream_client_2.video = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-video-3').srcObject = evt.streams[0];
					stream_client_3.video = evt.streams[0];
				}
			}else{
				if (client_call_number == 1){
					document.getElementById('client-video-2').srcObject = evt.streams[0];
					stream_client_2.video = evt.streams[0];
				}else if (client_call_number == 2){
					document.getElementById('client-video-3').srcObject = evt.streams[0];
					stream_client_3.video = evt.streams[0];
				}
			}
		}
	});
	


	return clients_pc[clients_pc.length-1];
}

function createPeerConnection() {
	var config = {
		sdpSemantics: 'unified-plan',
		iceServers: [{urls: ['stun:stun.l.google.com:19302']}]
	};
	

	pc = new RTCPeerConnection(config);
	//pc = new RTCPeerConnection();

	// connect audio
	pc.addEventListener('track', function(evt) {
		console.log("track");
		console.log(evt.streams[0].getTracks());
		//alert(pc.getTransceivers().length);
		if (evt.track.kind == 'audio'){
			$("#signal-audio").trigger("pause");
			$("#signal-audio").currentTime = 0; // Reset time
			document.getElementById('server-audio').srcObject = evt.streams[0];
			
			$("#control_call_button").addClass("d-none")
			$("#stop_call_button").removeClass("d-none")
		}else if (evt.track.kind == 'video'){
			document.getElementById('server-video').srcObject = evt.streams[0];
		}
	});
	


	return pc;
}

function timeoutPromise(ms, promise) {
  return new Promise((resolve, reject) => {
	const timeoutId = setTimeout(() => {
	  reject(new Error("promise timeout"))
	}, ms);
	promise.then(
	  (res) => {
		clearTimeout(timeoutId);
		resolve(res);
	  },
	  (err) => {
		clearTimeout(timeoutId);
		reject(err);
	  }
	);
  })
}
function negotiate() {
	return pc.createOffer({"offerToReceiveAudio":true,"offerToReceiveVideo":true}).then(function(offer) {
		return pc.setLocalDescription(offer);
	}).then(function() {
		// wait for ICE gathering to complete
		return new Promise(function(resolve) {
			console.log(pc.iceGatheringState);
			if (pc.iceGatheringState === 'complete') {
				resolve();
			} else {
				function checkState() {
					console.log(pc.iceGatheringState);
					if (pc.iceGatheringState === 'complete') {
						pc.removeEventListener('icegatheringstatechange', checkState);
						resolve();
					}
				}
				pc.addEventListener('icegatheringstatechange', checkState);

			}
		});
	}).then(function() {
		var offer = pc.localDescription;
		controller = new AbortController();
		signal = controller.signal;
		return timeoutPromise(30000, fetch('/offer', {
			body: JSON.stringify({
				sdp: offer.sdp,
				type: offer.type,
				"name":name,
				"surname":surname
			}),
			headers: {
				'Content-Type': 'application/json'
			},
			method: 'POST',
			signal
		}));
	}).then(function(response) {
		return response.json();
	}).then(function(answer) {
		if (answer.sdp == "" && answer.type == ""){
			console.log("call rejected 167");
			setTimeout(call_rejected, 1000);
			return null;
		}else{
			return pc.setRemoteDescription(answer);
		}
	}).catch(function(e) {
		setTimeout(call_rejected, 1000);
		//alert(e);
		console.log(e);
		return null;
	});
	
}

function negotiate_client(call_number) {
	return clients_pc[clients_pc.length-1].createOffer({"offerToReceiveAudio":true,"offerToReceiveVideo":true}).then(function(offer) {
		return clients_pc[clients_pc.length-1].setLocalDescription(offer);
	}).then(function() {
		// wait for ICE gathering to complete
		return new Promise(function(resolve) {
			console.log(clients_pc[clients_pc.length-1].iceGatheringState);
			if (clients_pc[clients_pc.length-1].iceGatheringState === 'complete') {
				resolve();
			} else {
				function checkStateClient() {
					console.log(clients_pc[clients_pc.length-1].iceGatheringState);
					if (clients_pc[clients_pc.length-1].iceGatheringState === 'complete') {
						clients_pc[clients_pc.length-1].removeEventListener('icegatheringstatechange', checkStateClient);
						resolve();
					}
				}
				clients_pc[clients_pc.length-1].addEventListener('icegatheringstatechange', checkStateClient);

			}
		});
	}).then(function() {
		var offer = clients_pc[clients_pc.length-1].localDescription;
		
		return fetch('/offer-client', {
			body: JSON.stringify({
				sdp: offer.sdp,
				type: offer.type,
				"desired_call":call_number,
				"call_number":local_call_number
			}),
			headers: {
				'Content-Type': 'application/json'
			},
			method: 'POST'
		});
	}).then(function(response) {
		return response.json();
	}).then(function(answer) {
		return clients_pc[clients_pc.length-1].setRemoteDescription(answer);
	}).catch(function(e) {
		//alert(e);
		console.log(e);
	});
	
}



function call_rejected(){
	console.log("call rejected");
	stop_peer_connection(false);
}

function stop_peer_connection(dc_message=true) {
	console.log("stop peer connection");
	//alert("stop peer connection");
	$("#signal-audio").trigger("pause");
	$("#signal-audio").currentTime = 0; // Reset time		
	// send disconnect message because iceconnectionstate slow to go in failed or in closed state
	try{
		if (dc.readyState == "open"){
			if (dc_message){
				dc.send("disconnected");
				console.log("sending disconnect message");
			}
		}
	}catch (e){
		console.log(e);
	}
	try{
		if (local_stream["audio"] != null){
			local_stream.audio.stop();
			local_stream.video.stop();
			local_stream = {"audio":null,"video":null};
		}
	}
	catch (e){
		console.log(e);
	}
	
	$("#control_call_button").removeClass("d-none")
	$("#stop_call_button").addClass("d-none")
	
	document.getElementById('client-video-1').srcObject = null;
	document.getElementById('server-video').srcObject = null;
	document.getElementById('server-audio').srcObject = null;
	document.getElementById('client-audio-2').srcObject = null;
	document.getElementById('client-video-2').srcObject = null;
	document.getElementById('client-audio-3').srcObject = null;
	document.getElementById('client-video-3').srcObject = null;

	try{
		if (controller != null){
			controller.abort();
		}
		if (dc.readyState != "open"){
			pc.close();
		}
	}catch (e){
		console.log(e);
	}

}

function stop_client_peer_connection(call_number) {
	if (local_call_number == 1){
		if (call_number == 2){
			document.getElementById('client-audio-2').srcObject = null;
			document.getElementById('client-video-2').srcObject = null;
		}else if (call_number == 3){
			document.getElementById('client-audio-3').srcObject = null;
			document.getElementById('client-video-3').srcObject = null;
		}
	}else if (local_call_number == 2){
		if (call_number == 1){
			document.getElementById('client-audio-2').srcObject = null;
			document.getElementById('client-video-2').srcObject = null;
		}else if (call_number == 3){
			document.getElementById('client-audio-3').srcObject = null;
			document.getElementById('client-video-3').srcObject = null;
		}
	}else{
		if (call_number == 1){
			document.getElementById('client-audio-2').srcObject = null;
			document.getElementById('client-video-2').srcObject = null;
		}else if (call_number == 2){
			document.getElementById('client-audio-3').srcObject = null;
			document.getElementById('client-video-3').srcObject = null;
		}
	}
}

function start_client(client_call_number,client_name,client_surname){
	if (local_call_number == 1){
		if (client_call_number == 2){
			$("#listener-2").html("Άλλος ακροατής: "+client_name+" "+client_surname+":");
		}else if (client_call_number == 3){
			$("#listener-3").html("Άλλος ακροατής: "+client_name+" "+client_surname+":");
		}
	}else if (local_call_number == 2){
		if (client_call_number == 1){
			$("#listener-2").html("Άλλος ακροατής: "+client_name+" "+client_surname+":");
		}else if (client_call_number == 3){
			$("#listener-3").html("Άλλος ακροατής: "+client_name+" "+client_surname+":");
		}
	}else{
		if (client_call_number == 1){
			$("#listener-2").html("Άλλος ακροατής: "+client_name+" "+client_surname+":");
		}else if (client_call_number == 2){
			$("#listener-3").html("Άλλος ακροατής: "+client_name+" "+client_surname+":");
		}
	}


	
	createLocalPeerConnection(client_call_number,client_name,client_surname);
	
	clients_pc[clients_pc.length-1].onclose = function() {
		// close data channel
		
		// close local audio / video
		clients_pc[clients_pc.length-1].getSenders().forEach(function(sender) {
			sender.track.stop();
		});

		// close transceivers
		if (clients_pc[clients_pc.length-1].getTransceivers) {
			clients_pc[clients_pc.length-1].getTransceivers().forEach(function(transceiver) {
				if (transceiver.stop) {
					transceiver.stop();
				}
			});
		}
		clients_pc.splice(clients_pc.length-1, 1);
		console.log("Local peer connection closed");
		if (local_call_number == 1){
			if (client_call_number ==2){
				stream_client_2 = stream_client_3;
				stream_client_3 = {"audio":null,"video":null};
				$("#listener-2").html($("#listener-3").html());
				$("#listener-3").html("Άλλος ακροατής:");
				document.getElementById('client-audio-2').srcObject = stream_client_2.audio;
				document.getElementById('client-audio-3').srcObject = null;
				document.getElementById('client-video-2').srcObject = stream_client_2.video;
				document.getElementById('client-video-3').srcObject = null;
			}else{//client_call_number = 3
				$("#listener-3").html("Άλλος ακροατής:");
				document.getElementById('client-audio-3').srcObject = null;
				document.getElementById('client-video-3').srcObject = null;			
			}
		}else{
			if (local_call_number == 2){
				if (client_call_number ==1){
					stream_client_2 = stream_client_3;
					stream_client_3 = {"audio":null,"video":null};
					$("#listener-2").html($("#listener-3").html());
					$("#listener-3").html("Άλλος ακροατής:");
					document.getElementById('client-audio-2').srcObject = stream_client_2.audio;
					document.getElementById('client-audio-3').srcObject = null;
					document.getElementById('client-video-3').srcObject = stream_client_2.video;
					document.getElementById('client-video-3').srcObject = null;
				
				}else{//client_call_number = 3
					stream_client_3 = {"audio":null,"video":null};
					$("#listener-3").html("Άλλος ακροατής:");
					document.getElementById('client-audio-3').srcObject = null;
					document.getElementById('client-video-3').srcObject = null;				
				}
			}else{//local_call_number = 3
				if (client_call_number ==1){
					stream_client_2 = stream_client_3;
					stream_client_3 = {"audio":null,"video":null};
					$("#listener-2").html($("#listener-3").html());
					$("#listener-3").html("Άλλος ακροατής:");
					document.getElementById('client-audio-2').srcObject = stream_client_2.audio;
					document.getElementById('client-audio-3').srcObject = null;
					document.getElementById('client-video-2').srcObject = stream_client_2.video;
					document.getElementById('client-video-3').srcObject = null;
				
				}else{//client_call_number = 2
					stream_client_3 = {"audio":null,"video":null};
					$("#listener-3").html("Άλλος ακροατής:");
					document.getElementById('client-audio-3').srcObject = null;
					document.getElementById('client-video-3').srcObject = null;				
				}
			}
		}
	};
	
	
	negotiate_client(client_call_number);
	
	
	constraints = {audio:true,video:true};
	
	/*navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		stream.getTracks().forEach(function(track) {
			clients_pc[clients_pc.length-1].addTrack(track, stream);
		});
		return negotiate_client(client_call_number);
		}, function(err) {
			alert('Could not acquire media: ' + err);
	});
	*/
}

function start(name,surname) {
	$("#control_call_button").addClass("d-none");
	$("#stop_call_button").removeClass("d-none");
	
	$("#signal-audio").trigger("play");
	pc = createPeerConnection();
	
	dc = pc.createDataChannel('chat', {"ordered": true});
	dc.onclose = function() {
		
	};
	dc.onopen = function() {
		
	};
	dc.onmessage = function(evt) {
		console.log(evt.data);
		data = JSON.parse(evt.data);
		if(data["type"] == "closing-call-1"){
			
			if (local_call_number == 1){
				if (closing == false){
					closing = true;
					stop_peer_connection();
				}
			}else{
				stop_client_peer_connection(1);
			}
		}else if (data["type"] == "closing-call-2"){
			if (local_call_number == 2){
				if (closing == false){
					closing = true;
					stop_peer_connection();
				}
			}else{
				stop_client_peer_connection(2);
			}
		}else if (data["type"] == "closing-call-3"){
			if (local_call_number == 3){
				if (closing == false){
					closing = true;
					stop_peer_connection();
				}
			}else{
				stop_client_peer_connection(3);
			}
		}
			
		
		if (data["type"] == "local_call_number"){
			local_call_number = data["call_number"];
			stream_client_1 = local_stream;
		}
		
		if (data["type"] == "new-client"){
			var client_call_number = data["call_number"]
			var client_name = data["name"]
			var client_surname = data["surname"]
			start_client(client_call_number,client_name,client_surname)
			
		}
		
	};

	pc.onconnectionstatechange = (event) => {
	   let newCS = pc.connectionState;
	   if (newCS == "disconnected" || newCS == "failed" || newCS == "closed") {
		  stop_peer_connection();
	   }
	}

	
	pc.onclose = function() {
		closing = true;
		stop_peer_connection(false);
		
		// close data channel
		if (dc) {
			dc.close();
		}

		// close local audio / video
		pc.getSenders().forEach(function(sender) {
			sender.track.stop();
		});

		// close transceivers
		if (pc.getTransceivers) {
			pc.getTransceivers().forEach(function(transceiver) {
				if (transceiver.stop) {
					transceiver.stop();
				}
			});
		}
		pc = null;
		console.log("Local peer connection closed");
		//alert("Local peer connection closed");
	
	};
	
	
	
	//negotiate();
	
	constraints = {audio:true,video:true};
	
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		//local_stream = stream;
		stream.getTracks().forEach(function(track) {
			
			try {
				pc.addTrack(track, stream);
				if (track.kind == "video"){
					//correct
					local_stream.video = track;
					document.getElementById('client-video-1').srcObject = stream;
				}else{
					local_stream.audio = track;
				}
				stream_client_1 = local_stream;
			} catch(e){
				//console.log(e);
			}
		});
		return negotiate();
		}, function(err) {
			alert('Could not acquire media: ' + err);
	});
	
	
}

$(document).ready(function(){
	$("#control_call_button").on( "click", function() {
		name = $("#name").val();
		surname = $("#surname").val();
		closing = false;
		controller = null;
		start(name,surname)
	});
	
	$("#stop_call_button").on( "click", function() {
		closing = true;
		stop_peer_connection();
	});
	//debug code
	/*$("#name").on( "focus",async function(){
		for(var i=0;i<10;i++){
			$("#control_call_button").click();
			await sleep(2000);
			$("#stop_call_button").click();
			await sleep(2000);
		}
	});
	*/
})

function sleep(ms) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

/*
window.addEventListener("beforeunload", function (e) {
	console.log("Before unload");
	fetch('/cancel_call', {
			body: JSON.stringify({}),
			headers: {
				'Content-Type': 'application/json'
			},
			method: 'POST'
		});
	const sleep = ms => new Promise(r => setTimeout(r, 5000));
});
*/