ARG BASE_CONTAINER=jupyter/scipy-notebook:dc9744740e12
FROM $BASE_CONTAINER

LABEL maintainer="Simon Hommel <simon.hommel@gmail.com>"

RUN conda install --quiet --yes \
    'numpy=1.18.*' \
    'plotly==4.5.4' \
	&& \
	conda install -c plotly plotly-orca==1.3.0 \
	&& \
    conda clean --all -f -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER