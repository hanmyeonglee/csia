export class Client{
    constructor(){
        this.key = this.generate();
        this.iv = this.generate();
    }

    generate() {
        let result = '';
        const characters = `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()'",./+-:;<>?=_|~[]`;
        const charactersLength = characters.length;
        let counter = 0;
        while (counter < 16) {
            result += characters.charAt(Math.floor(Math.random() * charactersLength));
            counter += 1;
        }
        return result;
    }

    uint8ArrayToBinary(u8Array) {
        let binaryString = '';
        for (let i = 0; i < u8Array.length; i++) {
            binaryString += String.fromCharCode(u8Array[i]);
        }
        return binaryString;
    }

    encrypt(mes){
        let key_enc = CryptoJS.enc.Utf8.parse(this.key);
        let iv_enc = CryptoJS.enc.Utf8.parse(this.iv);

        let message = CryptoJS.enc.Utf8.parse(mes);
        let encrypted = CryptoJS.AES.encrypt(message, key_enc, {
            iv : iv_enc,
            mode : CryptoJS.mode.CBC
        });

        return encrypted.toString();
    }

    decrypt(enc){
        let key_enc = CryptoJS.enc.Utf8.parse(this.key);
        let iv_enc = CryptoJS.enc.Utf8.parse(this.iv);

        let decrypted = CryptoJS.AES.decrypt(enc, key_enc, {
            iv : iv_enc,
            mode : CryptoJS.mode.CBC
        });

        return decrypted.toString(CryptoJS.enc.Utf8)

    }
}