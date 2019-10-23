FROM python:3

ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /ptr
COPY . /ptr
RUN pip install -r /ptr/requirements.txt

CMD ["bash"]
