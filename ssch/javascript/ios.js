const download = document.getElementById("downBtn");

download.addEventListener("click", async () => {
    const response = await fetch(`../files/CSIAOnline.app`);
    const file = await response.blob();
    const downloadUrl = window.URL.createObjectURL(file); // 해당 file을 가리키는 url 생성

    const anchorElement = document.createElement("a");
    anchorElement.setAttribute("hidden", true);
    document.body.appendChild(anchorElement);
    anchorElement.download = "CSIAOnline-win.app";
    anchorElement.href = downloadUrl; // href에 url 달아주기

    anchorElement.click(); // 코드 상으로 클릭을 해줘서 다운로드를 트리거

    document.body.removeChild(anchorElement); // cleanup - 쓰임을 다한 a 태그 삭제
    window.URL.revokeObjectURL(downloadUrl);
});