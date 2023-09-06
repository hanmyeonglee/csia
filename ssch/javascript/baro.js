const mobileBlur = document.getElementById('mb');
const desktopBlur = document.getElementById('db');
const mobileMain = document.getElementById('mm');
const desktopMain = document.getElementById('md');
mobileBlur.addEventListener("click", (e) => {
    mobileBlur.setAttribute("hidden", true);
    mobileMain.removeAttribute("hidden");
});
desktopBlur.addEventListener("click", (e) => {
    desktopMain.removeAttribute("hidden");
    desktopBlur.setAttribute("hidden", true);
});
mobileMain.addEventListener("click", (e) => {
    mobileMain.setAttribute("hidden", true);
    mobileBlur.removeAttribute("hidden");
});
desktopMain.addEventListener("click", (e) => {
    desktopMain.setAttribute("hidden", true);
    desktopBlur.removeAttribute("hidden");
});