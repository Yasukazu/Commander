# from https://nitratine.net/blog/post/python-gcm-encryption-tutorial/#generating-a-salt
from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import scrypt
from io import BytesIO
import os


BUFFER_SIZE = 1024 * 1024  # The size in bytes that we read, encrypt and write to at once


def encrypt( password: str, bytes_in: bytearray ) -> bytearray:
    # output_filename = input_filename + '.encrypted'  # You can name this anything, I'm just putting .encrypted on the end
    
    file_in = BytesIO(bytes_in)
    file_out = BytesIO()
    
    salt = get_random_bytes(32)  # Generate salt
    key = scrypt(password, salt, key_len=32, N=2**17, r=8, p=1)  # Generate a key using the password and salt
    file_out.write(salt)  # Write the salt to the top of the output file
    
    cipher = AES.new(key, AES.MODE_GCM)  # Create a cipher object to encrypt data
    file_out.write(cipher.nonce)  # Write out the nonce to the output file under the salt
    
    data = file_in.read(BUFFER_SIZE)  # Read in some of the file
    while len(data) != 0:  # Check if we need to encrypt anymore data
        encrypted_data = cipher.encrypt(data)  # Encrypt the data we read
        file_out.write(encrypted_data)  # Write the encrypted data to the output file
        data = file_in.read(BUFFER_SIZE)  # Read some more of the file to see if there is any more left
    
    tag = cipher.digest()  # Signal to the cipher that we are done and get the tag
    file_out.write(tag)
    return file_out.getvalue()

def decrypt( password: str, bytes_in: bytearray):
    file_in = BytesIO(bytes_in)
    file_out = BytesIO()
    
    salt = file_in.read(32)  # The salt we generated was 32 bits long
    key = scrypt(password, salt, key_len=32, N=2**17, r=8, p=1)  # Generate a key using the password and salt again
    
    nonce = file_in.read(16)  # The nonce is 16 bytes long
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    
    file_in_size = len(bytes_in) # os.path.getsize(input_filename)
    encrypted_data_size = file_in_size - 32 - 16 - 16  # Total - salt - nonce - tag = encrypted data
    
    for _ in range(int(encrypted_data_size / BUFFER_SIZE)):  # Identify how many loops of full buffer reads we need to do
        data = file_in.read(BUFFER_SIZE)  # Read in some data from the encrypted file
        decrypted_data = cipher.decrypt(data)  # Decrypt the data
        file_out.write(decrypted_data)  # Write the decrypted data to the output file
    data = file_in.read(int(encrypted_data_size % BUFFER_SIZE))  # Read whatever we have calculated to be left of encrypted data
    decrypted_data = cipher.decrypt(data)  # Decrypt the data
    file_out.write(decrypted_data)  # Write the decrypted data to the output file
    
    tag = file_in.read(16)
    try:
        cipher.verify(tag)
    except ValueError as e:
        raise e
    
    return file_out.getvalue()
    