var main_pc = {
	"name":"",
	"surname":"",
	"pc":null,
	"dc":null,
	"uid":null,
	"local_audio":null,
	"local_video":null,
	"remote_audio":null,
	"remote_video":null
};
var peer_connections = [];
var closing = false
var controller = null;
var signal;
var stop_time_out = null;

function start(name,surname) {
	$("#control_call_button").addClass("d-none");
	$("#stop_call_button").removeClass("d-none");
	
	$("#signal-audio").trigger("play");
	main_pc = createPeerConnection(main_pc);
	main_pc["name"] = name;
	main_pc["surname"] = surname;
	
	main_pc["dc"] = main_pc["pc"].createDataChannel('chat', {"ordered": true});
	
	main_pc["dc"].onmessage = function(evt) {
		data = JSON.parse(evt.data);
		if(data["type"] == "closing"){
			if (main_pc["uid"] == "uid"){	
				stop_peer_connection();
			}else{
				//stop_client_peer_connection(data["uid"]);
			}
		}
		
		if (data["type"] == "uid"){
			uid = data["uid"];
			main_pc["uid"] = uid;
			console.log(main_pc);
		}
		
		if (data["type"] == "new-client"){
			var uid = data["uid"];
			var client_name = data["name"];
			var client_surname = data["surname"];
			console.log("New client:");
			console.log(uid);
			console.log(client_name);
			console.log(client_surname);
			//start_client(uid,client_name,client_surname);
		}
		
	};

	main_pc["pc"].onconnectionstatechange = (event) => {
	   let newCS = main_pc["pc"].connectionState;
	   if (newCS == "disconnected" || newCS == "failed" || newCS == "closed") {
			stop_time_out = setTimeout(stop_with_time_out, 7000);	
	   }else{
			if (stop_time_out != null){
				clearTimeout(stop_time_out);
				stop_time_out = null;
			}
	   }
	}

	
	main_pc["pc"].onclose = function() {
		closing = true;
		stop_peer_connection();
		
		// close data channel
		if (main_pc["dc"]) {
			main_pc["dc"].close();
		}

		// close local audio / video
		main_pc["pc"].getSenders().forEach(function(sender) {
			sender.track.stop();
		});

		// close transceivers
		if (main_pc["pc"].getTransceivers) {
			main_pc["pc"].getTransceivers().forEach(function(transceiver) {
				if (transceiver.stop) {
					transceiver.stop();
				}
			});
		}
		main_pc["pc"] = null;
		$("#control_call_button").removeClass("d-none");
		$("#stop_call_button").addClass("d-none");
	};
	
	constraints = {audio:true,video:true};
	
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		stream.getTracks().forEach(function(track) {
			
			try {
				main_pc["pc"].addTrack(track, stream);
				if (track.kind == "video"){
					//correct
					main_pc["local_video"] = stream;
					document.getElementById('client-video-1').srcObject = stream;
				}else{
					main_pc["local_audio"] = stream;
				}
			} catch(e){
			}
		});
		return negotiate();
		}, function(err) {
			alert('Could not acquire media: ' + err);
	});
	
	
}

function createPeerConnection(pc) {
	var config = {
		sdpSemantics: 'unified-plan'
	};
	config.iceServers = [{ urls: ['stun:stun.l.google.com:19302'] }];

	pc["pc"] = new RTCPeerConnection(config);

	// connect audio
	pc["pc"].addEventListener('track', function(evt) {
		if (evt.track.kind == 'audio'){
			$("#signal-audio").trigger("pause");
			$("#signal-audio").currentTime = 0; // Reset time
			document.getElementById('server-audio').srcObject = evt.streams[0];
			
			$("#control_call_button").addClass("d-none")
			$("#stop_call_button").removeClass("d-none")
			
			pc["remote_audio"] = evt.streams[0];
		}else if (evt.track.kind == 'video'){
			document.getElementById('server-video').srcObject = evt.streams[0];
			pc["remote_video"] = evt.streams[0];
		}
	});
	
	return pc;
}

function negotiate() {
	return main_pc["pc"].createOffer({"offerToReceiveAudio":true,"offerToReceiveVideo":true}).then(function(offer) {
		return main_pc["pc"].setLocalDescription(offer);
	}).then(function() {
		// wait for ICE gathering to complete
		return new Promise(function(resolve) {
			if (main_pc["pc"].iceGatheringState === 'complete') {
				resolve();
			} else {
				function checkState() {
					if (main_pc["pc"].iceGatheringState === 'complete') {
						main_pc["pc"].removeEventListener('icegatheringstatechange', checkState);
						resolve();
					}
				}
				main_pc["pc"].addEventListener('icegatheringstatechange', checkState);

			}
		});
	}).then(function() {
		var offer = main_pc["pc"].localDescription;
		controller = new AbortController();
		signal = controller.signal;
		try{
			promise = timeoutPromise(60000, fetch('/offer', {
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
			return promise;
		}catch (error){
			console.log(error);
			stop_peer_connection();
		}
	}).then(function(response) {
		if (response.ok){
			return response.json();
		}else{
			stop_peer_connection();
		}
	}).then(function(answer) {
		console.log(answer);
		if (answer.sdp == "" && answer.type == ""){
			stop_peer_connection();
			return null;
		}else{
			return main_pc["pc"].setRemoteDescription(answer);
		}
	}).catch(function(e) {
		console.log(e);
		stop_peer_connection();
		return null;
	});
	
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

function stop_peer_connection(dc_message=true) {
	$("#signal-audio").trigger("pause");
	$("#signal-audio").currentTime = 0; // Reset time		
	// send disconnect message because iceconnectionstate slow to go in failed or in closed state
	try{
		if (main_pc["dc"].readyState == "open"){
			if (dc_message){
				main_pc["dc"].send(JSON.stringify({"type":"disconnected"}));
			}
		}
	}catch (e){
	}
	try{
		if (main_pc["local_audio"] != null){
			main_pc["local_audio"].stop();
			main_pc["local_video"].stop();
			main_pc["local_audio"] = null;
			main_pc["local_video"] = null;
		}
	}
	catch (e){
	}
	
	
	
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
		if (main_pc["dc"].readyState != "open"){
			main_pc["pc"].close();
		}
	}catch (e){
	}
	$("#control_call_button").removeClass("d-none")
	$("#stop_call_button").addClass("d-none")
}

function stop_with_time_out(){
	stop_peer_connection(false);
	stop_time_out = null;
}

$(document).ready(function(){
	$("#control_call_button").on( "click", function() {
		name = $("#name").val();
		surname = $("#surname").val();
		$("#me-name").html(name+" "+surname)
		closing = false;
		controller = null;
		start(name,surname);
	});
	$("#stop_call_button").on( "click", function() {
		closing = true;
		stop_peer_connection();
	});
})
