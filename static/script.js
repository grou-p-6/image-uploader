function preview() {
	const successLoaderDiv = document.getElementById("uploadSuccess");
	frame.src = URL.createObjectURL(event.target.files[0]);
	successLoaderDiv.style.display = "none";
}

function clearImage() {
	document.getElementById("formFile").value = null;
	frame.src = "";
}

function openModal(url) {
	const modalImg = document.getElementById("modalImage");
	modalImg.src = url;
	const imageModal = new bootstrap.Modal(document.getElementById("imageModal"));
	imageModal.show();
}

function appendImagesToContainer(imagesContainer, url) {
	const img = new Image();
	img.src = url;
	img.classList.add("shadow");
	img.classList.add("cursor_pointer");
	img.addEventListener("click", () => openModal(url));
	imagesContainer.appendChild(img);
}

function handleUpload(url) {
	const loader = document.getElementById("uploadLoader");
	const successLoader = document.getElementById("uploadSuccessAnim");
	const successLoaderDiv = document.getElementById("uploadSuccess");
	const imagesContainer = document.getElementById("imagesContainer");

	loader.style.display = "none";
	successLoaderDiv.style.display = "block";
	successLoader.play();
	clearImage();

	appendImagesToContainer(imagesContainer, url);
}

function sendImageToServer() {
	console.log("sending image to server");
	const fileInput = document.getElementById("formFile");
	const file = fileInput.files[0];

	if (file) {
		const loader = document.getElementById("uploadLoader");
		loader.style.display = "block";

		const formData = new FormData();
		formData.append("image", file);

		fetch("/api/upload", {
			method: "POST",
			body: formData,
		})
			.then((response) => response.json())
			.then((data) => {
				console.log(data);
				console.log(data.url);
				// Handle response from server here
				handleUpload(data.url);
			})
			.catch((error) => {
				console.error("Error:", error);
			});
	} else {
		alert("Please choose an image first.");
	}
}

async function fetchAndDisplayAllImages() {
	try {
		// Get the list of image URLs from the /api/images endpoint
		const response = await fetch("/api/images");
		const imageUrls = await response.json();

		const imagesContainer = document.getElementById("imagesContainer");

		// Loop through the image URLs and display each one
		for (let url of imageUrls.image_urls) {
			appendImagesToContainer(imagesContainer, url);
		}
	} catch (error) {
		console.error("Error fetching and displaying images:", error);
	}
}

// Call the function to fetch and display images
fetchAndDisplayAllImages();

function downloadImageHandler() {
	console.log("download button clicked");
	const modalImage = document.getElementById("modalImage");
	const imageUrl = modalImage.src;
	const imageName = imageUrl.split("/").pop(); // This will extract the image name from the URL. Modify as needed.

	downloadImage(imageUrl, imageName);
}

function downloadImage(url, name) {
	const anchor = document.createElement("a");
	anchor.href = url;
	anchor.download = name;
	document.body.appendChild(anchor);
	anchor.click();
	document.body.removeChild(anchor);
}
