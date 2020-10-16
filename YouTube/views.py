from django.shortcuts import render, redirect
from django.views import View
import requests, re
from YouTube.video_stream_format import video_streaming_datas
from django.contrib import messages
from bs4 import BeautifulSoup

# Create your views here.
def videoID(url):
	pattern = '[a-zA-Z0-9_-]+'
	vid = ''
	if 'v=' in url:
		vid = re.findall(pattern, url.split('v=')[1])
	elif 'be/' in url:
		vid = re.findall(pattern, url.split('be/')[1])
	if vid:
		return vid[0]
	return vid

def thumbnail(url, response):
	vid = videoID(url)
	pattern = r'https:\\?/\\?/i\.ytimg\.com\\?/vi\\?/{}\\?/[a-zA-Z0-9_-]+\.jpg'.format(vid)
	findthumbnail = re.findall(pattern, response)
	img = findthumbnail[0] if findthumbnail else ''
	img = img.replace('\\', '')
	return img

class Youtube(View):
    template_name = 'youtube.html'
    def get(self, request):
        return render(request, template_name=self.template_name)

    def post(self, request):
        video_url = request.POST.get('video-url')
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        response=requests.get(url=video_url,headers=headers).text
        
        soup = BeautifulSoup(response, 'lxml')
        vtitle = soup.title.text
        vthumbnail = thumbnail(video_url, response)

        pattern = r'https:\\/\\/[a-z0-9-]+\.googlevideo\.com.*\",\\\"mimeType\\\"'
        links = re.findall(pattern, response)[0] if re.findall(pattern, response) else ''
        video_links = sorted(links.replace(r'\\u0026', '&').split(','), key=len, reverse=True)
        get_video_links = [ link for link in video_links if 'googlevideo.com' in link ]

        video_link_quality = []

        for video_link in get_video_links:
            url = re.findall('https:.*', video_link)[0].strip('\\"').replace("\\", '')
            itags = int(re.findall('itag=[0-9]+', url)[0].split('=')[1]) if re.findall('itag=[0-9]+', url) else ''
            
            if itags:
                if itags in video_streaming_datas:
                    quality = video_streaming_datas[itags][-1]
                    vformat = video_streaming_datas[itags][0]
                    video_audio = video_streaming_datas[itags][1]
                    if vformat == 'mp4' and quality in ['144p', '240p', '360p', '480p', '720p']:
                        video_link_quality.append((quality, vformat, video_audio, url))
        
        if not video_link_quality:
            messages.info(request, "Sorry! Can't fetch URL")

        datas = {
            'download_url': video_link_quality,
            'thumbnail': vthumbnail,
            'title': vtitle,
        }
        
        return render(request, template_name=self.template_name, context=datas)