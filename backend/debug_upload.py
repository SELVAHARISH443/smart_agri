from app import app

client = app.test_client()
response = client.post('/api/soil-analysis', data={'image': (b'fake-image-data', 'soil.png')}, content_type='multipart/form-data')
print('status', response.status_code)
print('body', response.get_data(as_text=True))
print('content_type', response.content_type)
