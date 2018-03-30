#! python3

import threading, requests, logging, queue, os

def download(department, data_dir):
    department = department.lower()
    url = "https://catalog.colorado.edu/courses-a-z/{0}/".format(department)
    filepath = os.path.join(data_dir, department + ".html")

    resp = requests.get(url)
    resp.raise_for_status() # raises an exception if the request failed
    logging.info("saving {0} to {1}".format(department, filepath))
    with open(filepath, "w") as f:
        f.write(resp.text)


class CrawlerThread(threading.Thread):
    def __init__(self, dept_queue, data_dir):
        super(CrawlerThread, self).__init__()

        self.dept_queue = dept_queue
        self.data_dir = data_dir

    def scrape(self, dept_queue, maxretry=2):
        while not dept_queue.empty():
            dept = None
            try:
                dept, count = dept_queue.get_nowait()
                download(dept, self.data_dir)
            except queue.Empty:
                continue
            except Exception as e:
                logging.info('Error in department {0}: {1}'.format(dept, e))
                if count < maxretry:
                    dept_queue.put((dept, count + 1))
            finally:
                dept_queue.task_done()

    def run(self):
        self.scrape(self.dept_queue)


def crawl(depts, dir, nthreads):
    logging.info('Beggining new catalog data harvest')

    dept_queue = queue.Queue()
    for dept in depts:
        dept_queue.put((dept, 0))

    threads = []
    for i in range(nthreads):
        logging.info('Starting thread %d/%d.' % (i+1, nthreads))
        threads.append(CrawlerThread(dept_queue, dir))
        threads[i].start()

    for i in range(nthreads):
        threads[i].join()

    logging.info('Finished catalog data harvest.')
